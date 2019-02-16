==================
Subprocess support
==================

pytest-cov supports subprocesses and multiprocessing. However, there are a few pitfalls that need to be
explained.

Normally coverage writes the data via a pretty standard atexit handler. However, if the subprocess doesn't exit on its
own then the atexit handler might not run. Why that happens is best left to the adventurous to discover by waddling
though the python bug tracker.

For now pytest-cov provides opt-in workarounds for these problems.

If you use ``multiprocessing.Pool``
===================================

You need to make sure your ``multiprocessing.Pool`` gets a nice and clean exit:

.. code-block:: python

    from multiprocessing import Pool

    def f(x):
        return x*x

    if __name__ == '__main__':
        p = Pool(5)
        try:
            print(p.map(f, [1, 2, 3]))
        finally:       # <= THIS IS ESSENTIAL
            p.close()  # <= THIS IS ESSENTIAL
            p.join()   # <= THIS IS ESSENTIAL

Previously this guide recommended using ``multiprocessing.Pool``'s context manager API, however, that was wrong as
``multiprocessing.Pool.__exit__`` is an alias to ``multiprocessing.Pool.terminate``, and that doesn't always run the
finalizers (sometimes the problem in `cleanup_on_sigterm`_ will appear).

If you use ``multiprocessing.Process``
======================================

There's an identical issue when using the ``Process`` objects. Don't forget to use ``.join()``:

.. code-block:: python

    from multiprocessing import Process

    def f(name):
        print('hello', name)

    if __name__ == '__main__':
        p = Process(target=f, args=('bob',))
        try:
            p.start()
        finally:      # <= THIS IS ESSENTIAL
            p.join()  # <= THIS IS ESSENTIAL

.. _cleanup_on_sigterm:

If you abuse ``multiprocessing.Process.terminate``
==================================================

It appears that many people are using the ``terminate`` method and then get unreliable coverage results.

On Linux usually that means a SIGTERM gets sent to the process. Unfortunately Python don't have a default handler for
SIGTERM so you need to install your own. Because ``pytest-cov`` doesn't want to second-guess (not yet, add your thoughts
on the issue tracker if you disagree) it doesn't install a handler by default, but you can activate it by doing this:

.. code-block:: python

    try:
        from pytest_cov.embed import cleanup_on_sigterm
    except ImportError:
        pass
    else:
        cleanup_on_sigterm()


On Windows there's no nice way to do cleanup (no signal handlers) so you're left to your own devices.

If anything else
================

If you have custom signal handling, eg: you do reload on SIGHUP you should have something like this:

.. code-block:: python

    import os
    import signal

    def restart_service(frame, signum):
        os.exec( ... )  # or whatever your custom signal would do
    signal.signal(signal.SIGHUP, restart_service)

    try:
        from pytest_cov.embed import cleanup_on_signal
    except ImportError:
        pass
    else:
        cleanup_on_signal(signal.SIGHUP)

Note that both ``cleanup_on_signal`` and ``cleanup_on_sigterm`` will run the previous signal handler.

Alternatively you can do this:

    import os
    import signal

    try:
        from pytest_cov.embed import cleanup
    except ImportError:
        cleanup = None

    def restart_service(frame, signum):
        if cleanup is not None:
            cleanup()

        os.exec( ... )  # or whatever your custom signal would do
    signal.signal(signal.SIGHUP, restart_service)
