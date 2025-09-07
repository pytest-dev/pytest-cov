#!/usr/bin/env python

import re
from pathlib import Path

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    with Path(__file__).parent.joinpath(*names).open(encoding=kwargs.get('encoding', 'utf8')) as fh:
        return fh.read()


setup(
    name='pytest-cov',
    version='6.3.0',
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
        'pytest>=6.2.5',
        'coverage[toml]>=7.10.6',
        'pluggy>=1.2',
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
)
