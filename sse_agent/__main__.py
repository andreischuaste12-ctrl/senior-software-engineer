"""Execute com python -m sse_agent --help."""

import argparse
import json
import os
import sys

from . import __version__
from .agent import MAX_PAYLOAD, AgentError, Client, run
from .platforms import split_command
from .tools import Workspace


def positive(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError('Use um inteiro positivo.')
    return number


def positive_float(value: str) -> float:
    number = float(value)
    if not number > 0:
        raise argparse.ArgumentTypeError('Use um número positivo.')
    return number


def parse_checks(shell_style: list[str], json_style: list[str]) -> dict[str, list[str]]:
    """Converte --check NOME=COMANDO e --check-json NOME=ARRAY em {nome: argv}."""
    checks: dict[str, list[str]] = {}
    for item, as_json in [(item, False) for item in shell_style] + [
            (item, True) for item in json_style]:
        name, separator, command = item.partition('=')
        try:
            parts = json.loads(command) if as_json else split_command(command)
        except ValueError:
            raise AgentError('--check/--check-json com comando ilegível (aspas ou JSON inválidos).') from None
        if (not separator or not name.strip() or name in checks or
                not isinstance(parts, list) or not parts or
                any(not isinstance(part, str) or '\x00' in part for part in parts) or not parts[0]):
            raise AgentError('--check exige NOME=COMANDO com nome único e comando não vazio.')
        checks[name] = parts
    return checks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Agente de engenharia guiado pela skill do projeto.')
    parser.add_argument('task', help='Tarefa a executar; coloque entre aspas.')
    parser.add_argument('--version', action='version', version=f'sse_agent {__version__}')
    parser.add_argument('--workspace', default='.', help='Repositório autorizado (padrão: diretório atual).')
    parser.add_argument('--allow-write', action='store_true', help='Autorize criar/substituir arquivos de texto.')
    parser.add_argument('--check', action='append', default=[], metavar='NOME=COMANDO',
                        help='Autorize um comando sem shell, por exemplo tests=python -m unittest discover.')
    parser.add_argument('--check-json', action='append', default=[], metavar='NOME=JSON',
                        help='Autorize argumentos em array JSON, preservando caminhos com espaços.')
    parser.add_argument('--check-env', action='append', default=[], metavar='VARIAVEL',
                        help='Repasse esta variável de ambiente aos checks (por padrão só um '
                             'conjunto mínimo, sem segredos, é repassado). Repetível.')
    parser.add_argument('--max-steps', type=positive, default=12)
    parser.add_argument('--timeout', type=positive_float, default=60,
                        help='Timeout de cada check, em segundos.')
    parser.add_argument('--api-timeout', type=positive_float, default=120,
                        help='Timeout de cada chamada à API, em segundos.')
    parser.add_argument('--max-context-bytes', type=positive, default=MAX_PAYLOAD,
                        help='Tamanho máximo do payload enviado à API; resultados antigos de '
                             'ferramentas são compactados para caber.')
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if not args.task.strip():
            raise AgentError('Informe uma tarefa não vazia.')
        checks = parse_checks(args.check, args.check_json)
        workspace = Workspace(args.workspace, args.allow_write, checks, args.timeout,
                              pass_env=args.check_env)
        client = Client(os.environ.get('SSE_API_KEY') or os.environ.get('OPENAI_API_KEY'),
                        os.environ.get('SSE_MODEL'),
                        os.environ.get('SSE_BASE_URL', 'https://api.openai.com/v1'),
                        args.api_timeout, args.max_context_bytes)
        print('Arquivos lidos e tarefa serão enviados ao provedor configurado. '
              'Checks autorizados executam código local.', file=sys.stderr)
        result = run(client, workspace, args.task, args.max_steps,
                     notify=lambda name: print(f'Ferramenta: {name}', file=sys.stderr))
        print(result)
        return 0
    except (AgentError, OSError, ValueError) as exc:
        print(f'Erro: {exc}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('Interrompido; revise eventuais alterações locais.', file=sys.stderr)
        return 130


if __name__ == '__main__':
    # UTF-8 inclusive com stdout redirecionado no Windows.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    raise SystemExit(main())
