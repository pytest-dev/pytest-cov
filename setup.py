#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import io
import re
from distutils.command.build import build
from glob import glob
from itertools import chain
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import Command
from setuptools import find_packages
from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.easy_install import easy_install
from setuptools.command.install_lib import install_lib


def read(*names, **kwargs):
    with io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ) as fh:
        return fh.read()


class BuildWithPTH(build):
    def run(self, *args, **kwargs):
        build.run(self, *args, **kwargs)
        path = join(dirname(__file__), 'src', 'pytest-cov.pth')
        dest = join(self.build_lib, basename(path))
        self.copy_file(path, dest)


class EasyInstallWithPTH(easy_install):
    def run(self, *args, **kwargs):
        easy_install.run(self, *args, **kwargs)
        path = join(dirname(__file__), 'src', 'pytest-cov.pth')
        dest = join(self.install_dir, basename(path))
        self.copy_file(path, dest)


class InstallLibWithPTH(install_lib):
    def run(self, *args, **kwargs):
        install_lib.run(self, *args, **kwargs)
        path = join(dirname(__file__), 'src', 'pytest-cov.pth')
        dest = join(self.install_dir, basename(path))
        self.copy_file(path, dest)
        self.outputs = [dest]

    def get_outputs(self):
        return chain(install_lib.get_outputs(self), self.outputs)


class DevelopWithPTH(develop):
    def run(self, *args, **kwargs):
        develop.run(self, *args, **kwargs)
        path = join(dirname(__file__), 'src', 'pytest-cov.pth')
        dest = join(self.install_dir, basename(path))
        self.copy_file(path, dest)


class GeneratePTH(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        with open(join(dirname(__file__), 'src', 'pytest-cov.pth'), 'w') as fh:
            with open(join(dirname(__file__), 'src', 'pytest-cov.embed')) as sh:
                fh.write(
                    'import os, sys;'
                    'exec(%r)' % sh.read().replace('    ', ' ')
                )


setup(
    name='pytest-cov',
    version='2.12.1',
    license='MIT',
    description='Pytest plugin for measuring coverage.',
    long_description='%s\n%s' % (read('README.rst'), re.sub(':[a-z]+:`~?(.*?)`', r'``\1``', read('CHANGELOG.rst'))),
    author='Marc Schlaich',
    author_email='marc.schlaich@gmail.com',
    url='https://github.com/pytest-dev/pytest-cov',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Framework :: Pytest',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Testing',
        'Topic :: Utilities',
    ],
    keywords=[
        'cover', 'coverage', 'pytest', 'py.test', 'distributed', 'parallel',
    ],
    install_requires=[
        'pytest>=4.6',
        'coverage>=5.2.1',
        'toml'
    ],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
    extras_require={
        'testing': [
            'fields',
            'hunter',
            'process-tests',
            'six',
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
