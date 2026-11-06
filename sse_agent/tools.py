"""Ferramentas limitadas ao workspace escolhido pelo operador."""

from collections.abc import Iterator, Sequence
import hashlib
import os
from pathlib import Path, PureWindowsPath
import stat
import subprocess
import tempfile
from typing import Any

from .paths import matches_pattern
from .platforms import process_options, stop_process_tree

MAX_FILE_BYTES = 64_000          # texto devolvido ou gravado por chamada
MAX_EDIT_BYTES = 2_000_000       # maior arquivo que pode ser lido por faixa, buscado ou editado
MAX_SCANNED_FILES = 10_000
MAX_LISTED_FILES = 1000
MAX_SEARCH_RESULTS = 200
OUTPUT_LIMIT = 16_000
OUTPUT_HEAD = 2_000

# Diretórios com credenciais: nunca acessíveis.
SECRET_DIRS = {'.git', '.aws', '.ssh', '.kube', '.gnupg', '.docker'}
# Dependências e caches: não são código-fonte; nunca acessíveis.
DEPENDENCY_DIRS = {'.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache',
                   '.mypy_cache', '.ruff_cache', 'vendor', '.next', 'coverage'}
# Artefatos de build: ocultos da listagem apenas na raiz do workspace, porque
# pacotes legítimos (src/build, lib/target) podem usar esses nomes.
ARTIFACT_DIRS = {'dist', 'build', 'target'}
ENV_TEMPLATES = ('.env.example', '.env.sample', '.env.template')
SECRET_FILES = {'credentials', 'credentials.json', 'secrets.json', 'id_rsa', 'id_ed25519',
                'id_ecdsa', 'id_dsa', '.npmrc', '.netrc', '.pypirc', '.git-credentials',
                '.htpasswd', 'wp-config.php', 'secrets.yaml', 'secrets.yml'}

# Allowlist de variáveis repassadas aos checks (nomes em maiúsculas; LC_* também passa).
CHECK_ENV_ALLOWLIST = {
    'PATH', 'PATHEXT', 'HOME', 'USERPROFILE', 'USER', 'USERNAME', 'LOGNAME', 'LANG',
    'LANGUAGE', 'TERM', 'TZ', 'TMP', 'TEMP', 'TMPDIR', 'SYSTEMROOT', 'SYSTEMDRIVE',
    'WINDIR', 'COMSPEC', 'APPDATA', 'LOCALAPPDATA', 'PROGRAMDATA', 'PROGRAMFILES',
    'PROGRAMFILES(X86)', 'PROGRAMW6432', 'NUMBER_OF_PROCESSORS', 'PROCESSOR_ARCHITECTURE',
    'OS', 'VIRTUAL_ENV'}
NEVER_PASSED = {'SSE_API_KEY', 'OPENAI_API_KEY'}


def protected(part: str) -> bool:
    """Nome de componente que as ferramentas nunca leem, gravam ou listam."""
    lower = part.lower()
    if lower in SECRET_DIRS or lower in DEPENDENCY_DIRS or lower in SECRET_FILES:
        return True
    if lower == '.envrc' or lower == '.env' or lower.startswith('.env.'):
        return lower not in ENV_TEMPLATES
    return lower.endswith(('.pem', '.key', '.p12', '.pfx', '.jks', '.env', '.tfstate', '.tfvars')) or (
        '.tfstate.' in lower or lower.endswith('.tfvars.json'))


def linked(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))


def check_environment(extra: Sequence[str] = ()) -> dict[str, str]:
    """Ambiente mínimo dos checks; variáveis extras só por opt-in do operador."""
    allowed = (CHECK_ENV_ALLOWLIST | {name.upper() for name in extra}) - NEVER_PASSED
    environment = {key: value for key, value in os.environ.items()
                   if key.upper() in allowed or
                   (key.upper().startswith('LC_') and key.upper() not in NEVER_PASSED)}
    environment['PYTHONIOENCODING'] = 'utf-8'
    return environment


def split_lines(text: str) -> list[str]:
    """Linhas com terminadores preservados; só \\n delimita (como editores comuns)."""
    parts = text.split('\n')
    lines = [part + '\n' for part in parts[:-1]]
    if parts[-1]:
        lines.append(parts[-1])
    return lines


def uses_crlf(data: bytes) -> bool:
    crlf = data.count(b'\r\n')
    return crlf > 0 and crlf > data.count(b'\n') - crlf


def schema(name: str, description: str, properties: dict[str, Any],
           required: list[str]) -> dict[str, Any]:
    return {'type': 'function', 'function': {
        'name': name, 'description': description,
        'parameters': {'type': 'object', 'properties': properties,
                       'required': required, 'additionalProperties': False}}}


def integer_argument(value: Any, name: str, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f'{name} precisa ser um inteiro >= {minimum}.')
    return value


class Workspace:
    def __init__(self, root: str | Path, allow_write: bool = False,
                 checks: dict[str, list[str]] | None = None, timeout: float = 60,
                 pass_env: Sequence[str] = (), deny: Sequence[str] = (),
                 allow_files: Sequence[str] = ()) -> None:
        self.root = Path(root).resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError('O workspace precisa ser um diretório.')
        self.allow_write = allow_write
        self.checks = checks or {}
        self.timeout = timeout
        self.pass_env = tuple(pass_env)
        self.deny = tuple(deny)
        self.allow_files = tuple(allow_files)
        if any(not isinstance(pattern, str) or not pattern for pattern in (*self.deny, *self.allow_files)):
            raise ValueError('Padrões de acesso precisam ser textos não vazios.')

    def denied(self, relative: str) -> bool:
        return any(matches_pattern(relative.casefold(), pattern.casefold()) for pattern in self.deny)

    def allowed_file(self, relative: str) -> bool:
        return not self.allow_files or any(matches_pattern(relative.casefold(), pattern.casefold())
                                           for pattern in self.allow_files)

    # ------------------------------------------------------------------ caminhos

    def path(self, relative: Any, directory: bool = False) -> Path:
        if not isinstance(relative, str) or not relative or '\x00' in relative:
            raise ValueError('Caminho relativo inválido.')
        path = Path(relative.replace('\\', '/'))
        reserved = {'CON', 'PRN', 'AUX', 'NUL', 'CONIN$', 'CONOUT$'} | {
            prefix + number for prefix in ('COM', 'LPT') for number in '123456789¹²³'}
        if (path.is_absolute() or PureWindowsPath(relative).anchor or
                any(part == '..' or protected(part) or ':' in part or
                    part.endswith((' ', '.')) or part.split('.')[0].upper() in reserved
                    for part in path.parts)):
            raise ValueError('Caminho fora do escopo ou arquivo protegido.')
        candidate = self.root
        for part in path.parts:
            candidate = candidate / part
            if self.denied(candidate.relative_to(self.root).as_posix()):
                raise ValueError('Caminho excluído pelo operador.')
            if linked(candidate):
                raise ValueError('Links simbólicos e reparse points não são permitidos nas ferramentas de arquivo.')
        if not candidate.resolve().is_relative_to(self.root):
            raise ValueError('Caminho fora do workspace.')
        if not directory and not self.allowed_file(candidate.relative_to(self.root).as_posix()):
            raise ValueError('Arquivo fora da lista autorizada pelo operador.')
        return candidate

    def definitions(self) -> list[dict[str, Any]]:
        definitions = [
            schema('list_files', 'Liste arquivos visíveis (até 1000). Opcional: pattern '
                   '(glob, ex.: "*.py" ou "src/**/*.ts") para filtrar.',
                   {'pattern': {'type': 'string'}, 'directory': {'type': 'string'}}, []),
            schema('search_text', 'Busque um texto literal nos arquivos (como grep -F). '
                   'Devolve caminho, linha e trecho. Use antes de ler arquivos inteiros.',
                   {'query': {'type': 'string'}, 'pattern': {'type': 'string'},
                    'directory': {'type': 'string'},
                    'ignore_case': {'type': 'boolean'},
                    'max_results': {'type': 'integer', 'minimum': 1, 'maximum': MAX_SEARCH_RESULTS}},
                   ['query']),
            schema('read_file', 'Leia um arquivo UTF-8 e obtenha o SHA-256 do arquivo inteiro '
                   'antes de editar. Arquivos acima de 64000 bytes exigem start_line/end_line '
                   '(1-indexadas, inclusivas); a resposta traz total_lines.',
                   {'path': {'type': 'string'}, 'start_line': {'type': 'integer', 'minimum': 1},
                    'end_line': {'type': 'integer', 'minimum': 1}}, ['path']),
        ]
        if self.allow_write:
            definitions.append(schema(
                'replace_in_file', 'Substitua um trecho exato por outro num arquivo existente. '
                'Prefira a write_file para mudanças pontuais. Exige o SHA-256 lido; falha se old '
                'não existir ou não for único (a menos que replace_all). Preserva CRLF.',
                {'path': {'type': 'string'}, 'old': {'type': 'string'}, 'new': {'type': 'string'},
                 'expected_sha256': {'type': 'string'}, 'replace_all': {'type': 'boolean'}},
                ['path', 'old', 'new', 'expected_sha256']))
            definitions.append(schema(
                'write_file', 'Grave UTF-8 (até 64000 bytes). Para arquivo existente use o SHA-256 '
                'lido; para novo use null. Preserva CRLF de arquivo existente. Não apaga arquivos.',
                {'path': {'type': 'string'}, 'content': {'type': 'string'},
                 'expected_sha256': {'type': ['string', 'null']}},
                ['path', 'content', 'expected_sha256']))
        if self.checks:
            definitions.append(schema(
                'run_check', 'Execute um check definido pelo operador. Nomes: ' +
                ', '.join(self.checks),
                {'name': {'type': 'string', 'enum': list(self.checks)}}, ['name']))
        return definitions

    # ------------------------------------------------------------------ leitura

    def _walk(self, directory: str = '.') -> Iterator[str | None]:
        """Caminhos relativos legíveis; yield None sinaliza que o limite de varredura foi atingido."""
        scanned = 0
        start = self.path(directory, directory=True)
        if not start.is_dir():
            raise ValueError('Diretório de busca não encontrado.')
        for base, dirs, files in os.walk(start, followlinks=False):
            at_root = Path(base) == self.root
            dirs[:] = sorted(d for d in dirs if not protected(d) and
                             not (at_root and d.lower() in ARTIFACT_DIRS) and
                             not self.denied((Path(base) / d).relative_to(self.root).as_posix()) and
                             not linked(Path(base) / d))
            for name in sorted(files):
                scanned += 1
                if scanned > MAX_SCANNED_FILES:
                    yield None
                    return
                relative = (Path(base) / name).relative_to(self.root).as_posix()
                if (protected(name) or linked(Path(base) / name) or self.denied(relative) or
                        not self.allowed_file(relative)):
                    continue
                yield (Path(base) / name).relative_to(self.root).as_posix()

    def list_files(self, pattern: str | None = None, directory: str = '.') -> dict[str, Any]:
        if pattern is not None and not isinstance(pattern, str):
            raise ValueError('pattern precisa ser texto.')
        found: list[str] = []
        for relative in self._walk(directory):
            if relative is None:
                return {'files': found, 'truncated': True}
            if not matches_pattern(relative, pattern):
                continue
            found.append(relative)
            if len(found) >= MAX_LISTED_FILES:
                return {'files': found, 'truncated': True}
        return {'files': found, 'truncated': False}

    def _load(self, relative: str) -> tuple[Path, bytes]:
        target = self.path(relative)
        if not target.is_file():
            raise ValueError('Arquivo regular não encontrado.')
        with target.open('rb') as stream:
            data = stream.read(MAX_EDIT_BYTES + 1)
        if len(data) > MAX_EDIT_BYTES:
            raise ValueError(f'Arquivo excede o limite de {MAX_EDIT_BYTES} bytes.')
        return target, data

    def read_file(self, path: str, start_line: int | None = None,
                  end_line: int | None = None) -> dict[str, Any]:
        _, data = self._load(path)
        digest = hashlib.sha256(data).hexdigest()
        if start_line is None and end_line is None:
            if len(data) > MAX_FILE_BYTES:
                raise ValueError(f'Arquivo excede o limite de {MAX_FILE_BYTES} bytes; '
                                 'use start_line e end_line para ler por faixa.')
            return {'path': path, 'content': data.decode('utf-8'), 'sha256': digest}
        lines = split_lines(data.decode('utf-8'))
        start = 1 if start_line is None else integer_argument(start_line, 'start_line')
        end = len(lines) if end_line is None else integer_argument(end_line, 'end_line')
        if start > end:
            raise ValueError('start_line não pode ser maior que end_line.')
        if lines and start > len(lines):
            raise ValueError(f'start_line além do fim do arquivo ({len(lines)} linhas).')
        encoded = ''.join(lines[start - 1:end]).encode('utf-8')
        truncated = len(encoded) > MAX_FILE_BYTES
        if truncated:
            encoded = encoded[:MAX_FILE_BYTES]
            newline = encoded.rfind(b'\n')
            if newline >= 0:
                encoded = encoded[:newline + 1]
        content = encoded.decode('utf-8', errors='ignore')
        returned = len(split_lines(content))
        return {'path': path, 'content': content, 'sha256': digest, 'start_line': start,
                'end_line': start + returned - 1 if returned else start,
                'total_lines': len(lines), 'truncated': truncated}

    def search_text(self, query: str, pattern: str | None = None, ignore_case: bool = False,
                    max_results: int = 100, directory: str = '.') -> dict[str, Any]:
        if not isinstance(query, str) or not query:
            raise ValueError('query precisa ser um texto não vazio.')
        if pattern is not None and not isinstance(pattern, str):
            raise ValueError('pattern precisa ser texto.')
        limit = min(integer_argument(max_results, 'max_results'), MAX_SEARCH_RESULTS)
        needle = query.lower() if ignore_case else query
        matches: list[dict[str, Any]] = []
        for relative in self._walk(directory):
            if relative is None:
                return {'matches': matches, 'truncated': True}
            if not matches_pattern(relative, pattern):
                continue
            try:
                with self.path(relative).open('rb') as stream:
                    data = stream.read(MAX_EDIT_BYTES + 1)
                if len(data) > MAX_EDIT_BYTES or b'\x00' in data:
                    continue
                text = data.decode('utf-8')
            except (OSError, ValueError):
                continue  # ilegível, binário ou fora da política: ignore silenciosamente
            for number, line in enumerate(text.split('\n'), 1):
                if needle in (line.lower() if ignore_case else line):
                    position = (line.lower() if ignore_case else line).find(needle)
                    begin = max(0, position - 60)
                    matches.append({'path': relative, 'line': number,
                                    'text': line.rstrip('\r')[begin:begin + 200]})
                    if len(matches) >= limit:
                        return {'matches': matches, 'truncated': True}
        return {'matches': matches, 'truncated': False}

    # ------------------------------------------------------------------ escrita

    def _require_write(self) -> None:
        if not self.allow_write:
            raise ValueError('Escrita não autorizada; use --allow-write.')

    def _replace_existing(self, relative: str, target: Path, data: bytes,
                          expected_sha256: str) -> None:
        """Substitui atomicamente, revalidando caminho e hash imediatamente antes."""
        mode = stat.S_IMODE(target.stat().st_mode)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(data)
                stream.flush()
                if os.name != 'nt':
                    os.fchmod(stream.fileno(), mode)
            # O handle precisa estar fechado antes de substituir/remover no Windows.
            self.path(relative)
            if hashlib.sha256(self._load(relative)[1]).hexdigest() != expected_sha256:
                raise ValueError('Arquivo alterado durante a gravação.')
            os.replace(temporary, target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def write_file(self, path: str, content: str,
                   expected_sha256: str | None) -> dict[str, Any]:
        self._require_write()
        if not isinstance(content, str):
            raise ValueError('Conteúdo precisa ser texto.')
        data = content.encode('utf-8')
        if len(data) > MAX_FILE_BYTES:
            raise ValueError(f'Conteúdo excede o limite de {MAX_FILE_BYTES} bytes.')
        target = self.path(path)
        if not target.parent.is_dir():
            raise ValueError('O diretório pai precisa existir; não é criado automaticamente.')
        if target.exists():
            _, current = self._load(path)
            if not expected_sha256 or expected_sha256 != hashlib.sha256(current).hexdigest():
                raise ValueError('Arquivo mudou ou não foi lido; leia novamente antes de gravar.')
            if uses_crlf(current) and b'\r' not in data:
                data = data.replace(b'\n', b'\r\n')  # preserve o fim de linha do arquivo
            self._replace_existing(path, target, data, expected_sha256)
        else:
            if expected_sha256 is not None:
                raise ValueError('Arquivo não existe; para criar use expected_sha256 null.')
            with target.open('xb') as stream:
                stream.write(data)
        return {'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'written': True}

    def replace_in_file(self, path: str, old: str, new: str, expected_sha256: str,
                        replace_all: bool = False) -> dict[str, Any]:
        self._require_write()
        if not isinstance(replace_all, bool):
            raise ValueError('replace_all precisa ser booleano.')
        if not isinstance(old, str) or not old or not isinstance(new, str):
            raise ValueError('old precisa ser texto não vazio e new precisa ser texto.')
        if not isinstance(expected_sha256, str) or not expected_sha256:
            raise ValueError('Informe o SHA-256 lido do arquivo.')
        target, current = self._load(path)
        if expected_sha256 != hashlib.sha256(current).hexdigest():
            raise ValueError('Arquivo mudou ou não foi lido; leia novamente antes de editar.')
        text = current.decode('utf-8')
        if uses_crlf(current):
            if '\r' not in old:
                old = old.replace('\n', '\r\n')
            if '\r' not in new:
                new = new.replace('\n', '\r\n')
        count = text.count(old)
        if count == 0:
            raise ValueError('Trecho old não encontrado; confira espaços, indentação e quebras.')
        if count > 1 and not replace_all:
            raise ValueError(f'Trecho old aparece {count} vezes; amplie o contexto ou use replace_all.')
        # Calcule o tamanho UTF-8 antes de materializar uma expansão potencialmente
        # enorme. count segue as mesmas ocorrências não sobrepostas de str.replace.
        replacements = count if replace_all else 1
        result_size = len(current) + replacements * (len(new.encode('utf-8')) - len(old.encode('utf-8')))
        if result_size > MAX_EDIT_BYTES:
            raise ValueError(f'Resultado excede o limite de {MAX_EDIT_BYTES} bytes.')
        data = text.replace(old, new, replacements).encode('utf-8')
        self._replace_existing(path, target, data, expected_sha256)
        return {'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'written': True,
                'replacements': replacements}

    # ------------------------------------------------------------------ checks

    def run_check(self, name: str) -> dict[str, Any]:
        if name not in self.checks:
            raise ValueError('Check não autorizado.')
        with tempfile.TemporaryFile() as output:
            process = subprocess.Popen(self.checks[name], cwd=self.root, stdin=subprocess.DEVNULL,
                                       stdout=output, stderr=subprocess.STDOUT,
                                       env=check_environment(self.pass_env), **process_options())
            timed_out = False
            try:
                process.wait(timeout=self.timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                stop_process_tree(process)
            except BaseException:
                stop_process_tree(process)
                raise
            size = output.seek(0, os.SEEK_END)
            if size <= OUTPUT_LIMIT:
                output.seek(0)
                text = output.read().decode('utf-8', errors='replace')
            else:
                # Falhas costumam estar no fim: mantenha o início e, principalmente, o final.
                output.seek(0)
                head = output.read(OUTPUT_HEAD)
                output.seek(size - (OUTPUT_LIMIT - OUTPUT_HEAD))
                tail = output.read()
                text = (head.decode('utf-8', errors='replace') +
                        f'\n[... {size - OUTPUT_LIMIT} bytes omitidos ...]\n' +
                        tail.decode('utf-8', errors='replace'))
        return {'name': name, 'exit_code': process.returncode, 'timed_out': timed_out,
                'output': text, 'truncated': size > OUTPUT_LIMIT, 'output_bytes': size}

    def execute(self, name: str, arguments: Any) -> dict[str, Any]:
        enabled = {item['function']['name'] for item in self.definitions()}
        if name not in enabled:
            return {'error': 'Ferramenta desconhecida ou não autorizada.'}
        try:
            if not isinstance(arguments, dict):
                raise ValueError('Argumentos precisam ser um objeto JSON.')
            result: dict[str, Any] = getattr(self, name)(**arguments)
            return result
        except (OSError, ValueError, TypeError) as error:
            return {'error': str(error)}
        except Exception as error:  # falha inesperada não deve derrubar a tarefa paga
            return {'error': f'Falha inesperada na ferramenta ({type(error).__name__}).'}
