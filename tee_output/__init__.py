import fcntl
import os
import struct
import subprocess
import sys
import termios
import tty
from dataclasses import dataclass, field
from typing import List, Optional, TextIO, Tuple, Union

tees = []


@dataclass
class Tee:
    orig_stdout: TextIO = field(init=False)
    stdout_pipe_proc: Optional[Tuple[TextIO, subprocess.Popen]] = field(init=False, default=None)

    orig_stderr: TextIO = field(init=False)
    stderr_pipe_proc: Optional[Tuple[TextIO, subprocess.Popen]] = field(init=False, default=None)

    def __post_init__(self):
        tees.append(self)  # Do not let this get GC'd
        self.orig_stdout = _dup(sys.stdout)
        self.orig_stderr = _dup(sys.stderr)

    def to(self, stdout, stderr):
        if not isinstance(stdout, list):
            stdout = [stdout]
        if not isinstance(stderr, list):
            stderr = [stderr]

        old_stdout_pipe_proc = self.stdout_pipe_proc
        self.stdout_pipe_proc = _tee(self.orig_stdout, stdout, stdout=self.orig_stdout)
        self.stdout = stdout
        old_stderr_pipe_proc = self.stderr_pipe_proc
        self.stderr_pipe_proc = _tee(self.orig_stderr, stderr, stdout=self.orig_stdout)
        self.stderr = stderr

        self.resume()

        # One sharp edge is that if you've spawned a subprocess with
        # the redirected stdout/stderr, the tee processes will not
        # die. In that case maybe we should set a timeout, or just
        # leak them? Not sure.
        if old_stdout_pipe_proc is not None:
            pipe, proc = old_stdout_pipe_proc
            pipe.close()
            proc.wait()
        if old_stderr_pipe_proc is not None:
            pipe, proc = old_stderr_pipe_proc
            pipe.close()
            proc.wait()
        return self

    def resume(self):
        os.dup2(self.stdout_pipe_proc[0].fileno(), sys.stdout.fileno())
        os.dup2(self.stderr_pipe_proc[0].fileno(), sys.stderr.fileno())

    def pause(self):
        os.dup2(self.orig_stdout.fileno(), sys.stdout.fileno())
        os.dup2(self.orig_stderr.fileno(), sys.stderr.fileno())


def _tee(src, to, stdout):
    if src.isatty():
        w, r = os.openpty()
        flags = termios.tcgetattr(src.fileno())
        termios.tcsetattr(w, termios.TCSANOW, flags)
        termios.tcsetattr(r, termios.TCSANOW, flags)
    else:
        r, w = os.pipe()

    r = os.fdopen(r, "rb", buffering=0)
    w = os.fdopen(w, "wb", buffering=0)

    if src.isatty():
        tty.setraw(r)

        # Copy window size
        packed = fcntl.ioctl(sys.stdin, termios.TIOCGWINSZ, struct.pack("HHHH", 0, 0, 0, 0))
        fcntl.ioctl(r, termios.TIOCSWINSZ, packed)

        def set_ctty():
            w.close()
            fcntl.ioctl(r, termios.TIOCSCTTY, 0)

    else:

        def set_ctty():
            w.close()

    for path in to:
        os.makedirs(os.path.dirname(path), exist_ok=True)

    proc = subprocess.Popen(
        ["parent-lifetime", "--term", "tee", "-a"] + list(to),
        stdin=r,
        start_new_session=True,
        stderr=subprocess.DEVNULL,
        stdout=stdout,
        preexec_fn=set_ctty,
    )
    r.close()
    return w, proc


def _dup(src):
    src = os.dup(src.fileno())
    src = os.fdopen(src, "rb", buffering=0)
    return src


def tee(stdout: Union[str, List[str]], stderr: Union[List[str], str]):
    return Tee().to(stdout=stdout, stderr=stderr)


if __name__ == "__main__":
    t = Tee()
    t.to("/tmp/out.orig", "/tmp/err.orig")
    t.to("/tmp/out.new", "/tmp/err.new")
    breakpoint()
