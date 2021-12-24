# Tee Output

`tee-output` is a Python library to tee standard output / standard
error from the current process into a logfile. Unlike doing a shell
redirection (i.e. `python myscript.py 2>&1 | tee /tmp/log`),
`tee-output` preserves terminal semantics, so `breakpoint()` etc
continue to work.

Basic usage:

```
from tee_output import tee
tee("/tmp/log.out", "/tmp/log.err")
```

After running the above, your standard output will stream to
`/tmp/stdout.out` in addition to the terminal; your standard error will
stream to `/tmp/stdout.err` in addition to the terminal.

You can also provide a list of locations to `tee`:

```
from tee_output import tee
tee(["/tmp/log.out", "/tmp/log.combined"], ["/tmp/log.err", "/tmp/log.combined"])
```

This will additionally create a file `/tmp/log.combined` which
contains the interleaved standard output and error, such as you see in
your terminal.
