from pytest_cov import pytest_cov
from setuptools import setup

setup(name='pytest-cov',
      version='0.6',
      description='py.test plugin for coverage reporting with support for both centralised and distributed testing',
      long_description=open('README.txt').read().strip(),
      author='Meme Dough',
      author_email='memedough@gmail.com',
      url='http://bitbucket.org/memedough/pytest-cov/overview',
      packages=['pytest_cov'],
      install_requires=['py>=1.2.2',
                        'pytest-xdist>=1.2',
                        'coverage>=3.3.1'],
      entry_points={'pytest11': ['pytest_cov = pytest_cov.pytest_cov']},
      license='MIT License',
      zip_safe=False,
      keywords='py.test pytest cover coverage distributed parallel',
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Software Development :: Testing'])
