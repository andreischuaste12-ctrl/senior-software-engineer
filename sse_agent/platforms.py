"""Adaptação de argumentos e encerramento de processos para Windows e POSIX."""

import os
import shlex
import signal
import subprocess
import sys
from typing import TypedDict


class ProcessOptions(TypedDict, total=False):
    creationflags: int
    start_new_session: bool


def split_command(command: str) -> list[str]:
    if sys.platform != 'win32':
        return shlex.split(command)
    # Use a interpretação nativa de aspas e barras, sem cmd.exe/PowerShell.
    import ctypes
    from ctypes import wintypes
    count = ctypes.c_int()
    parse = ctypes.WinDLL('shell32', use_last_error=True).CommandLineToArgvW
    parse.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    parse.restype = ctypes.POINTER(wintypes.LPWSTR)
    free = ctypes.WinDLL('kernel32', use_last_error=True).LocalFree
    free.argtypes = [ctypes.c_void_p]
    free.restype = ctypes.c_void_p
    if not command.strip():
        return []
    argv = parse(command, ctypes.byref(count))
    if not argv:
        raise OSError(ctypes.get_last_error(), 'Não foi possível interpretar o comando Windows.')
    try:
        return [argv[index] for index in range(count.value)]
    finally:
        free(ctypes.cast(argv, ctypes.c_void_p))


def process_options() -> ProcessOptions:
    if sys.platform == 'win32':
        return {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP}
    return {'start_new_session': True}


def stop_process_tree(process: subprocess.Popen[bytes]) -> None:
    if sys.platform == 'win32':
        system_root = os.environ.get('SystemRoot', r'C:\Windows')
        taskkill = os.path.join(system_root, 'System32', 'taskkill.exe')
        try:
            subprocess.run([taskkill, '/PID', str(process.pid), '/T', '/F'],
                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired):
            pass
        if process.poll() is None:
            process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait()
