pytest_plugins = "pytester",


def pytest_configure(config):
    config.option.runpytest = 'subprocess'
