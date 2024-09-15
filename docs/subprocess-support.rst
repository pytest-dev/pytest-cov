==================
Subprocess support
==================

Normally coverage writes the data via a pretty standard atexit handler. However, if the subprocess doesn't exit on its
own then the atexit handler might not run. Why that happens is best left to the adventurous to discover by waddling
through the Python bug tracker.

pytest-cov supports subprocesses, and works around these atexit limitations. However, there are a few pitfalls that need to be explained.

But first, how does pytest-cov's subprocess support works?

pytest-cov packaging injects a pytest-cov.pth into the installation. This file effectively runs this at *every* python startup:

.. code-block:: python

    if 'COV_CORE_SOURCE' in os.environ:
        try:
            from pytest_cov.embed import init
            init()
        except Exception as exc:
            sys.stderr.write(
                "pytest-cov: Failed to setup subprocess coverage. "
                "Environ: {0!r} "
                "Exception: {1!r}\n".format(
                    dict((k, v) for k, v in os.environ.items() if k.startswith('COV_CORE')),
                    exc
                )
            )

The pytest plugin will set this ``COV_CORE_SOURCE`` environment variable thus any subprocess that inherits the environment variables
(the default behavior) will run ``pytest_cov.embed.init`` which in turn sets up coverage according to these variables:

* ``COV_CORE_SOURCE``
* ``COV_CORE_CONFIG``
* ``COV_CORE_DATAFILE``
* ``COV_CORE_BRANCH``
* ``COV_CORE_CONTEXT``

Why does it have the ``COV_CORE`` you wonder? Well, it's mostly historical reasons: long time ago pytest-cov depended on a cov-core package
that implemented common functionality for pytest-cov, nose-cov and nose2-cov. The dependency is gone but the convention is kept. It could
be changed but it would break all projects that manually set these intended-to-be-internal-but-sadly-not-in-reality environment variables.

Coverage's subprocess support
=============================

Now that you understand how pytest-cov works you can easily figure out that using
`coverage's recommended <https://coverage.readthedocs.io/en/latest/subprocess.html>`_ way of dealing with subprocesses,
by either having this in a ``.pth`` file or ``sitecustomize.py`` will break everything:

.. code-block::

    import coverage; coverage.process_startup()  # this will break pytest-cov

Do not do that as that will restart coverage with the wrong options.

If you use ``multiprocessing``
==============================

Builtin support for multiprocessing was dropped in pytest-cov 4.0.
This support was mostly working but very broken in certain scenarios (see `issue 82408 <https://github.com/python/cpython/issues/82408>`_)
and made the test suite very flaky and slow.

However, there is `builtin multiprocessing support in coverage <https://coverage.readthedocs.io/en/latest/config.html#run-concurrency>`_
and you can migrate to that. All you need is this in your preferred configuration file (example: ``.coveragerc``):

.. code-block:: ini

    [run]
    concurrency = multiprocessing
    parallel = true
    sigterm = true

Now as a side-note, it's a good idea in general to properly close your Pool by using ``Pool.join()``:

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


.. _cleanup_on_sigterm:

Signal handlers
===============

pytest-cov provides a signal handling routines, mostly for special situations where you'd have custom signal handling that doesn't
allow atexit to properly run and the now-gone multiprocessing support:

* ``pytest_cov.embed.cleanup_on_sigterm()``
* ``pytest_cov.embed.cleanup_on_signal(signum)`` (e.g.: ``cleanup_on_signal(signal.SIGHUP)``)

If you use multiprocessing
--------------------------

It is not recommanded to use these signal handlers with multiprocessing as registering signal handlers will cause deadlocks in the pool,
see: https://bugs.python.org/issue38227).

If you got custom signal handling
---------------------------------

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
------------------

On Windows you can register a handler for SIGTERM but it doesn't actually work. It will work if you
`os.kill(os.getpid(), signal.SIGTERM)` (send SIGTERM to the current process) but for most intents and purposes that's
completely useless.

Consequently this means that if you use multiprocessing you got no choice but to use the close/join pattern as described
above. Using the context manager API or `terminate` won't work as it relies on SIGTERM.

However you can have a working handler for SIGBREAK (with some caveats):

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

The `caveats <https://stefan.sofa-rockers.org/2013/08/15/handling-sub-process-hierarchies-python-linux-os-x/>`_ being
roughly:

* you need to deliver ``signal.CTRL_BREAK_EVENT``
* it gets delivered to the whole process group, and that can have unforeseen consequences
