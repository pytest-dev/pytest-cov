from pytest_cover import pytest_cover
from setuptools import setup

setup(name='pytest-cover',
      version='0.5',
      description='py.test plugin for coverage collection with support for both centralised and distributed testing',
      long_description=pytest_cover.__doc__.strip(),
      author='Meme Dough',
      author_email='memedough@gmail.com',
      url='http://bitbucket.org/memedough/pytest-cover/overview',
      packages=['pytest_cover'],
      install_requires=['py>=1.2.2',
                        'pytest-xdist>=1.2',
                        'coverage>=3.3.1'],
      entry_points={'pytest11': ['pytest_cover = pytest_cover.pytest_cover']},
      license='MIT License',
      zip_safe=False,
      keywords='py.test pytest cover coverage distributed parallel',
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Software Development :: Testing'])
