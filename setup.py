#!/usr/bin/env python

import re
from itertools import chain
from pathlib import Path

from setuptools import Command
from setuptools import find_packages
from setuptools import setup

try:
    # https://setuptools.pypa.io/en/latest/deprecated/distutils-legacy.html
    from setuptools.command.build import build
except ImportError:
    from distutils.command.build import build

from setuptools.command.develop import develop
from setuptools.command.easy_install import easy_install
from setuptools.command.install_lib import install_lib


def read(*names, **kwargs):
    with Path(__file__).parent.joinpath(*names).open(encoding=kwargs.get('encoding', 'utf8')) as fh:
        return fh.read()


class BuildWithPTH(build):
    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)
        path = str(Path(__file__).parent / 'src' / 'pytest-cov.pth')
        dest = str(Path(self.build_lib) / Path(path).name)
        self.copy_file(path, dest)


class EasyInstallWithPTH(easy_install):
    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)
        path = str(Path(__file__).parent / 'src' / 'pytest-cov.pth')
        dest = str(Path(self.install_dir) / Path(path).name)
        self.copy_file(path, dest)


class InstallLibWithPTH(install_lib):
    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)
        path = str(Path(__file__).parent / 'src' / 'pytest-cov.pth')
        dest = str(Path(self.install_dir) / Path(path).name)
        self.copy_file(path, dest)
        self.outputs = [dest]

    def get_outputs(self):
        return chain(super().get_outputs(), self.outputs)


class DevelopWithPTH(develop):
    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)
        path = str(Path(__file__).parent / 'src' / 'pytest-cov.pth')
        dest = str(Path(self.install_dir) / Path(path).name)
        self.copy_file(path, dest)


class GeneratePTH(Command):
    user_options = ()

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        with Path(__file__).parent.joinpath('src', 'pytest-cov.pth').open('w') as fh:
            with Path(__file__).parent.joinpath('src', 'pytest-cov.embed').open() as sh:
                fh.write(f'import os, sys;exec({sh.read().replace("    ", " ")!r})')


setup(
    name='pytest-cov',
    version='6.2.0',
    license='MIT',
    description='Pytest plugin for measuring coverage.',
    long_description='{}\n{}'.format(read('README.rst'), re.sub(':[a-z]+:`~?(.*?)`', r'``\1``', read('CHANGELOG.rst'))),
    author='Marc Schlaich',
    author_email='marc.schlaich@gmail.com',
    url='https://github.com/pytest-dev/pytest-cov',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[path.stem for path in Path('src').glob('*.py')],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Framework :: Pytest',
        'Intended Audience :: Developers',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Testing',
        'Topic :: Utilities',
    ],
    project_urls={
        'Documentation': 'https://pytest-cov.readthedocs.io/',
        'Changelog': 'https://pytest-cov.readthedocs.io/en/latest/changelog.html',
        'Issue Tracker': 'https://github.com/pytest-dev/pytest-cov/issues',
    },
    keywords=[
        'cover',
        'coverage',
        'pytest',
        'py.test',
        'distributed',
        'parallel',
    ],
    python_requires='>=3.9',
    install_requires=[
        'pytest>=4.6',
        'coverage[toml]>=7.5',
    ],
    extras_require={
        'testing': [
            'fields',
            'hunter',
            'process-tests',
            'pytest-xdist',
            'virtualenv',
        ]
    },
    entry_points={
        'pytest11': [
            'pytest_cov = pytest_cov.plugin',
        ],
    },
    cmdclass={
        'build': BuildWithPTH,
        'easy_install': EasyInstallWithPTH,
        'install_lib': InstallLibWithPTH,
        'develop': DevelopWithPTH,
        'genpth': GeneratePTH,
    },
)
