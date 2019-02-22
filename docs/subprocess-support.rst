==================
Subprocess support
==================

Normally coverage writes the data via a pretty standard atexit handler. However, if the subprocess doesn't exit on its
own then the atexit handler might not run. Why that happens is best left to the adventurous to discover by waddling
though the Python bug tracker.

pytest-cov supports subprocesses and multiprocessing, and works around these atexit limitations. However, there are a
few pitfalls that need to be explained.

If you use ``multiprocessing.Pool``
===================================

In **pytest-cov 2.6** and older a multiprocessing finalizer is automatically registered. The finalizer will only run
reliably if the pool is closed. If you use ``multiprocessing.Pool.terminate`` or the context manager API (``__exit__``
will just call ``terminate``) then the workers can get SIGTERM and then the finalizers won't run or complete in time.
Thus you need to make sure your ``multiprocessing.Pool`` gets a nice and clean exit:

.. code-block:: python

    from multiprocessing import Pool

    def f(x):
        return x*x

    if __name__ == '__main__':
        p = Pool(5)
        try:
            print(p.map(f, [1, 2, 3]))
        finally:
            p.close()  # Marks the pool as closed.
            p.join()   # Waits for workers to exit.


In **pytest-cov 2.7** a SIGTERM handler is also automatically registered if multiprocessing is used. Thus you can use
the convenient context manger API:

.. code-block:: python

    from multiprocessing import Pool

    def f(x):
        return x*x

    if __name__ == '__main__':
        with Pool(5) as p:
            print(p.map(f, [1, 2, 3]))

If you use ``multiprocessing.Process``
======================================

There's similar issue when using the ``Process`` objects. Don't forget to use ``.join()``:

.. code-block:: python

    from multiprocessing import Process

    def f(name):
        print('hello', name)

    if __name__ == '__main__':
        p = Process(target=f, args=('bob',))
        try:
            p.start()
        finally:
            p.join()  # necessary so that the Process exists before the test suite exits (thus coverage is collected)

.. _cleanup_on_sigterm:

If you got custom signal handling
=================================

**pytest-cov 2.6** has a rudimentary ``pytest_cov.embed.cleanup_on_sigterm`` you can use to register a SIGTERM handler
that flushes the coverage data.

**pytest-cov 2.7** adds a ``pytest_cov.embed.cleanup_on_signal`` function and changes the implementation to be more
robust: the handler will call the previous handler (if you had previously registered any), and is re-entrant (will
defer extra signals if delivered while the handler runs).

For example, if you reload on SIGHUP you should have something like this:

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

.. code-block:: python

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

If you use Windows
==================

On Windows you can register a handler for SIGTERM but it doesn't actually work. However you can have a working handler
for SIGBREAK:

.. code-block:: python

    import os
    import signal

    def shutdown(frame, signum):
        # your app's shutdown or whatever
    signal.signal(signal.SIGBREAK, shutdown)

    try:
        from pytest_cov.embed import cleanup_on_signal
    except ImportError:
        pass
    else:
        cleanup_on_signal(signal.SIGBREAK)

Note that `SIGBREAK is tricky
<https://stefan.sofa-rockers.org/2013/08/15/handling-sub-process-hierarchies-python-linux-os-x/>`_:

* you need to deliver ``signal.CTRL_BREAK_EVENT``
* it gets delivered to the whole process group, and that can have unforeseen consequences
