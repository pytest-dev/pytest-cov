from setuptools import setup, find_packages


setup(
    name='example',
    packages=find_packages('src'),
    package_dir={'': 'src'},
)
