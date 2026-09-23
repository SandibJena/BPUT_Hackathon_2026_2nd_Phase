"""Run and supervise both local development servers (POSIX/WSL)."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def stop(process: subprocess.Popen) -> None:
    # Kill the process group, including npm/Next and Uvicorn reload children.
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def main() -> int:
    processes: list[subprocess.Popen] = []
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        processes.append(subprocess.Popen(
            [sys.executable, '-m', 'uvicorn', 'app.main:app', '--reload',
             '--host', '127.0.0.1', '--port', '8000'],
            cwd=ROOT / 'backend', start_new_session=True,
        ))
        processes.append(subprocess.Popen(
            ['npm', 'run', 'dev', '--', '--hostname', '127.0.0.1'],
            cwd=ROOT / 'frontend', start_new_session=True,
        ))
        print('Frontend: http://localhost:3000 | API: http://127.0.0.1:8000/health', flush=True)
        while all(p.poll() is None for p in processes):
            time.sleep(0.5)
        print('A development server stopped; shutting down both.', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0
    finally:
        for process in processes:
            stop(process)


if __name__ == '__main__':
    raise SystemExit(main())
