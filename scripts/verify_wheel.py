"""Build and run the installed wheel outside the checkout without API calls or credentials."""

from pathlib import Path
import subprocess
import sys
import tempfile
import venv


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    with tempfile.TemporaryDirectory(prefix='sse wheel ') as temporary:
        directory = Path(temporary)
        subprocess.run([sys.executable, '-m', 'pip', 'wheel', '--no-deps', '--wheel-dir',
                        str(directory), str(root)], check=True)
        venv.create(directory / 'env', with_pip=True)
        python = directory / 'env' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
        wheel, = directory.glob('*.whl')
        subprocess.run([str(python), '-m', 'pip', 'install', '--no-deps', '--no-index', str(wheel)], check=True)
        command = ('from sse_agent.agent import instructions; from sse_agent.tools import Workspace; '
                   'from importlib.resources import files; '
                   'assert "# Senior Software Engineer" in instructions(Workspace(".")); '
                   'assert files("sse_skill").joinpath("NOTICE").is_file(); '
                   'assert files("sse_skill").joinpath("references").joinpath("api-currency.md").is_file(); '
                   'print("Installed wheel and resources are available outside the checkout.")')
        subprocess.run([str(python), '-I', '-c', command], cwd=directory, check=True)
        subprocess.run([str(python), '-I', '-m', 'sse_agent.evals', 'list'], cwd=directory, check=True)


if __name__ == '__main__':
    main()
