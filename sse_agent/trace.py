"""Content-free JSONL trace of an agent run, for debugging the agent itself.

Events carry tool names, sizes, durations, and outcomes. They never carry file contents,
tool arguments, or task text, so a trace is safe to share when the workspace is not.
"""

import json
import os
from pathlib import Path
import time
from types import TracebackType
from typing import Any


class JsonlTrace:
    def __init__(self, path: str | Path) -> None:
        target = Path(path)
        if target.is_dir():
            raise ValueError('The trace path must be a file, not a directory.')
        if not target.parent.is_dir():
            raise ValueError('The trace file directory does not exist.')
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, 'O_NOFOLLOW', 0)
        try:
            descriptor = os.open(target, flags, 0o600)
        except OSError:
            raise ValueError('The trace file could not be opened.') from None
        self.stream = os.fdopen(descriptor, 'a', encoding='utf-8')

    def __call__(self, event: dict[str, Any]) -> None:
        self.stream.write(json.dumps({'time': round(time.time(), 3), **event}, ensure_ascii=False) + '\n')
        self.stream.flush()

    def close(self) -> None:
        self.stream.close()

    def __enter__(self) -> 'JsonlTrace':
        return self

    def __exit__(self, kind: type[BaseException] | None, value: BaseException | None,
                 traceback: TracebackType | None) -> None:
        self.close()
