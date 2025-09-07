==================
Subprocess support
==================

Subprocess support was removed in pytest-cov 7.0 due to various complexities resulting from coverage's own subprocess support.
To migrate you should change your coverage config to have at least this:

.. code-block:: ini

    [run]
    patch = subprocess

Or if you use pyproject.toml:

.. code-block:: toml

    [tool.coverage.run]
    patch = ["subprocess"]

Note that if you enable the subprocess patch then ``parallel = true`` is automatically set.

If it still doesn't produce the same coverage as before you may need to enable more patches, see the `coverage config <https://coverage.readthedocs.io/en/latest/config.html#run-patch>`_ and `subprocess <https://coverage.readthedocs.io/en/latest/subprocess.html>`_ documentation.
