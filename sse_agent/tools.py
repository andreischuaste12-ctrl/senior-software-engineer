"""Ferramentas limitadas ao workspace escolhido pelo operador."""

import hashlib
import os
from pathlib import Path
import stat
import subprocess
import tempfile


MAX_FILE_BYTES = 64_000
EXCLUDED = {'.git', '.aws', '.ssh', '.venv', 'venv', 'node_modules', '__pycache__',
            'dist', 'build', 'target', '.pytest_cache'}


def sensitive(part):
    lower = part.lower()
    return (part in EXCLUDED or lower.startswith('.env') or
            lower.endswith(('.pem', '.key', '.p12', '.pfx')) or
            lower in {'credentials', 'credentials.json', 'secrets.json', 'id_rsa', 'id_ed25519'})


def schema(name, description, properties, required):
    return {'type': 'function', 'function': {
        'name': name, 'description': description,
        'parameters': {'type': 'object', 'properties': properties,
                       'required': required, 'additionalProperties': False}}}


class Workspace:
    def __init__(self, root, allow_write=False, checks=None, timeout=60):
        self.root = Path(root).resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError('O workspace precisa ser um diretório.')
        self.allow_write = allow_write
        self.checks = checks or {}
        self.timeout = timeout

    def path(self, relative):
        if not isinstance(relative, str) or not relative or '\x00' in relative:
            raise ValueError('Caminho relativo inválido.')
        path = Path(relative)
        if path.is_absolute() or any(part == '..' or sensitive(part) for part in path.parts):
            raise ValueError('Caminho fora do escopo ou arquivo protegido.')
        candidate = self.root
        for part in path.parts:
            candidate = candidate / part
            if candidate.is_symlink():
                raise ValueError('Links simbólicos não são permitidos nas ferramentas de arquivo.')
        if not candidate.resolve().is_relative_to(self.root):
            raise ValueError('Caminho fora do workspace.')
        return candidate

    def definitions(self):
        definitions = [
            schema('list_files', 'Liste arquivos visíveis; resultados limitados a 1000.', {}, []),
            schema('read_file', 'Leia um arquivo UTF-8 e obtenha seu SHA-256 antes de editar.',
                   {'path': {'type': 'string'}}, ['path']),
        ]
        if self.allow_write:
            definitions.append(schema(
                'write_file', 'Grave UTF-8. Para arquivo existente use o SHA-256 lido; '
                'para novo use null. Não apaga arquivos.',
                {'path': {'type': 'string'}, 'content': {'type': 'string'},
                 'expected_sha256': {'type': ['string', 'null']}},
                ['path', 'content', 'expected_sha256']))
        if self.checks:
            definitions.append(schema(
                'run_check', 'Execute um check definido pelo operador. Nomes: ' +
                ', '.join(self.checks),
                {'name': {'type': 'string', 'enum': list(self.checks)}}, ['name']))
        return definitions

    def list_files(self):
        found = []
        scanned = 0
        for base, dirs, files in os.walk(self.root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not sensitive(d) and
                             not (Path(base) / d).is_symlink())
            for name in sorted(files):
                scanned += 1
                if scanned > 10_000:
                    return {'files': found, 'truncated': True}
                if sensitive(name) or (Path(base) / name).is_symlink():
                    continue
                found.append((Path(base) / name).relative_to(self.root).as_posix())
                if len(found) >= 1000:
                    return {'files': found, 'truncated': True}
        return {'files': found, 'truncated': False}

    def read_file(self, path):
        target = self.path(path)
        if not target.is_file():
            raise ValueError('Arquivo regular não encontrado.')
        with target.open('rb') as stream:
            data = stream.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise ValueError('Arquivo excede o limite de 64000 bytes.')
        return {'path': path, 'content': data.decode('utf-8'),
                'sha256': hashlib.sha256(data).hexdigest()}

    def write_file(self, path, content, expected_sha256):
        if not self.allow_write:
            raise ValueError('Escrita não autorizada; use --allow-write.')
        if not isinstance(content, str):
            raise ValueError('Conteúdo precisa ser texto.')
        data = content.encode('utf-8')
        if len(data) > MAX_FILE_BYTES:
            raise ValueError('Conteúdo excede o limite de 64000 bytes.')
        target = self.path(path)
        if not target.parent.is_dir():
            raise ValueError('O diretório pai precisa existir; não é criado automaticamente.')
        if target.exists():
            current = self.read_file(path)
            if not expected_sha256 or expected_sha256 != current['sha256']:
                raise ValueError('Arquivo mudou ou não foi lido; leia novamente antes de gravar.')
            mode = stat.S_IMODE(target.stat().st_mode)
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
                temporary = Path(stream.name)
                try:
                    stream.write(data)
                    stream.flush()
                    os.fchmod(stream.fileno(), mode)
                except BaseException:
                    temporary.unlink(missing_ok=True)
                    raise
            try:
                # Reconfere a fronteira imediatamente antes da substituição.
                self.path(path)
                if self.read_file(path)['sha256'] != expected_sha256:
                    raise ValueError('Arquivo alterado durante a gravação.')
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
        else:
            if expected_sha256 is not None:
                raise ValueError('Arquivo não existe; para criar use expected_sha256 null.')
            with target.open('xb') as stream:
                stream.write(data)
        return {'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'written': True}

    def run_check(self, name):
        if name not in self.checks:
            raise ValueError('Check não autorizado.')
        environment = {key: value for key, value in os.environ.items()
                       if key not in {'SSE_API_KEY', 'OPENAI_API_KEY'}}
        with tempfile.TemporaryFile() as output:
            process = subprocess.Popen(self.checks[name], cwd=self.root, stdin=subprocess.DEVNULL,
                                       stdout=output, stderr=subprocess.STDOUT,
                                       start_new_session=True, env=environment)
            timed_out = False
            try:
                process.wait(timeout=self.timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                # O CLI inicial suporta sistemas POSIX; encerra também subprocessos.
                import signal
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            except BaseException:
                import signal
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise
            output.seek(0)
            data = output.read(16_001)
        return {'name': name, 'exit_code': process.returncode, 'timed_out': timed_out,
                'output': data[:16_000].decode('utf-8', errors='replace'),
                'truncated': len(data) > 16_000}

    def execute(self, name, arguments):
        enabled = {item['function']['name'] for item in self.definitions()}
        if name not in enabled:
            return {'error': 'Ferramenta desconhecida ou não autorizada.'}
        try:
            if not isinstance(arguments, dict):
                raise ValueError('Argumentos precisam ser um objeto JSON.')
            return getattr(self, name)(**arguments)
        except (OSError, ValueError, TypeError) as error:
            return {'error': str(error)}
