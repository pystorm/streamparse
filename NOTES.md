## notes on remote debugging

I have a basic remote debugger working in ``streamparse.debug``.

You can run it with ``python debug.py`` and then connect to the port indicated
with ``telnet`` or ``nc``, e.g.

    telnet 7999

This will then bring you the pdb prompt.

So, the idea here is that ``set_trace()`` would run inside a Spout or Bolt when
it crashes, and then you could connect using some ``fabric`` magic (ssh into
appropriate worker, then run telnet/nc).

Celery has another good idea here, which is to use SIGUSR1/SIGUSR2 for logging
and debugging, respectively. SIGUSR1 does a "cry" command, which dumps all
current stack frames:

    def install_cry_handler(sig='SIGUSR1'):
        def cry_handler(*args):
            """Signal handler logging the stacktrace of all active threads."""
            with in_sighandler():
                safe_say(cry())
        platforms.signals[sig] = cry_handler

Meanwhile, SIGUSR2 does an RDB command, which installs the socket-based PDB:

    def install_rdb_handler(sig='SIGUSR2'):
        def rdb_handler(*args):
            """Signal handler setting a rdb breakpoint at the current frame."""
            with in_sighandler():
                from celery.contrib.rdb import set_trace, _frame
                frame = args[1] if args else _frame().f_back
                set_trace(frame)
            platforms.signals[sig] = rdb_handler

Pretty interesting. But there are still some open issues:

- the pdb-over-socket thing is kinda icky; ideally it would be a true "client", but
  I have a feeling that doing this properly may be more effort than it's worth

- given that there may be many failing Storm tasks (processes), are we going to want
  to be able to debug them all? or should the strategy be to find a single failing node
  and just go for that

- will pdb-over-telnet work when *within* a shell session under fabric, remotely on
  another server? 

