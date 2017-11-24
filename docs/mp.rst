=======================
Multiprocessing support
=======================

Although pytest-cov supports multiprocessing there are few pitfalls that need to be explained.

Abusing ``Process.terminate``
=============================

It appears that many people are using the ``terminate`` method and then get unreliable coverage results.

On Linux usually that means a SIGTERM gets sent to the process. Unfortunately Python don't have a default handler for SIGTERM
so you need to install your own. Because ``pytest-cov`` doesn't want to second-guess (not yet, add your thoughts on the issue
tracker if you disagree) it doesn't install a handler by default, but you can activate it by doing anything like:

.. code-block:: python

    from pytest_cov.embed import cleanup_on_sigterm
    cleanup_on_sigterm()

    # alternatively you can do this

    from pytest_cov.embed import cleanup

    def my_handler(signum, frame):
        cleanup()
        # custom cleanup
    signal.signal(signal.SIGTERM, my_handler)

On Windows there's no nice way to do cleanup (no signal handlers) so you're left to your own devices.

Ungraceful Pool shutdown
========================

Another problem is when using the ``Pool`` object. If you run some work on a pool in a test you're not guaranteed to get all
the coverage data unless you use the ``join`` method.

Eg:

.. code-block:: python

    from multiprocessing import Pool

    def f(x):
        return x*x

    if __name__ == '__main__':
        with Pool(5) as p:
            print(p.map(f, [1, 2, 3]))

        p.join()  # <= THIS IS ESSENTIAL


Ungraceful Process shutdown
===========================

There's an identical issue when using the ``Process`` objects. Don't forget to use ``.join()``:

.. code-block:: python

    from multiprocessing import Process

    def f(name):
        print('hello', name)

    if __name__ == '__main__':
        p = Process(target=f, args=('bob',))
        p.start()

        p.join()  # <= THIS IS ESSENTIAL
