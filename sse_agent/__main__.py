"""Execute com python -m sse_agent --help."""

import argparse
import os
import shlex
import sys

from .agent import AgentError, Client, run
from .tools import Workspace


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError('Use um inteiro positivo.')
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description='Agente de engenharia guiado pela skill do projeto.')
    parser.add_argument('task', help='Tarefa a executar; coloque entre aspas.')
    parser.add_argument('--workspace', default='.', help='Repositório autorizado (padrão: diretório atual).')
    parser.add_argument('--allow-write', action='store_true', help='Autorize criar/substituir arquivos de texto.')
    parser.add_argument('--check', action='append', default=[], metavar='NOME=COMANDO',
                        help='Autorize um comando sem shell, por exemplo tests=python -m unittest discover.')
    parser.add_argument('--max-steps', type=positive, default=12)
    parser.add_argument('--timeout', type=positive, default=60, help='Timeout por chamada de API/check, em segundos.')
    args = parser.parse_args(argv)
    try:
        if os.name != 'posix':
            raise AgentError('Esta versão do CLI suporta Linux e macOS (POSIX).')
        if not args.task.strip():
            raise AgentError('Informe uma tarefa não vazia.')
        checks = {}
        for item in args.check:
            name, separator, command = item.partition('=')
            parts = shlex.split(command)
            if not separator or not name.strip() or name in checks or not parts:
                raise AgentError('--check exige NOME=COMANDO com nome único e comando não vazio.')
            checks[name] = parts
        workspace = Workspace(args.workspace, args.allow_write, checks, args.timeout)
        client = Client(os.environ.get('SSE_API_KEY') or os.environ.get('OPENAI_API_KEY'),
                        os.environ.get('SSE_MODEL'),
                        os.environ.get('SSE_BASE_URL', 'https://api.openai.com/v1'), args.timeout)
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
    raise SystemExit(main())
