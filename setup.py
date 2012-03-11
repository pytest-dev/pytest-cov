import setuptools
import sys
import os

# The name of the path file must appear after easy-install.pth so that
# cov_core has been added to the sys.path and cov_core_init can be
# imported.
PTH_FILE_NAME = 'init_cov_core.pth'

# The line in the path file must begin with "import" so that site.py will exec it.
PTH_FILE = '''\
import os; os.environ.get('COV_CORE_SOURCE') and __import__('cov_core_init').init()
'''

UNKNOWN_SITE_PACKAGES_DIR = '''
Failed to find site-packages or dist-packages dir to put pth file in.
Sub processes will not have coverage collected.

To measure sub processes put the following in a file called %s:
%s
''' % (PTH_FILE_NAME, PTH_FILE)

setuptools.setup(name='cov-core',
                 version='1.5',
                 description='plugin core for use by pytest-cov, nose-cov and nose2-cov',
                 long_description=open('README.txt').read().strip(),
                 author='Meme Dough',
                 author_email='memedough@gmail.com',
                 url='http://bitbucket.org/memedough/cov-core/overview',
                 py_modules=['cov_core',
                             'cov_core_init'],
                 install_requires=['coverage>=3.4'],
                 license='MIT License',
                 zip_safe=False,
                 keywords='cover coverage',
                 classifiers=['Development Status :: 4 - Beta',
                              'Intended Audience :: Developers',
                              'License :: OSI Approved :: MIT License',
                              'Operating System :: OS Independent',
                              'Programming Language :: Python',
                              'Programming Language :: Python :: 2.4',
                              'Programming Language :: Python :: 2.5',
                              'Programming Language :: Python :: 2.6',
                              'Programming Language :: Python :: 2.7',
                              'Programming Language :: Python :: 3.0',
                              'Programming Language :: Python :: 3.1',
                              'Topic :: Software Development :: Testing'])

if sys.argv[1] in ('install', 'develop'):
    for path in sys.path:
        if (path.endswith('site-packages')) or (path.endswith('dist-packages') and 'local' in path):
            path = os.path.join(path, PTH_FILE_NAME)
            pth_file = open(path, 'w')
            pth_file.write(PTH_FILE)
            pth_file.close()
            sys.stdout.write('\nWrote pth file for subprocess measurement to %s\n' % path)
            break
    else:
        sys.stdout.write(UNKNOWN_SITE_PACKAGES_DIR)
