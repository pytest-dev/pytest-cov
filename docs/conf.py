import os

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.ifconfig',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.extlinks',
]
if os.getenv('SPELLCHECK'):
    extensions += ('sphinxcontrib.spelling',)
    spelling_show_suggestions = True
    spelling_lang = 'en_US'

source_suffix = '.rst'
master_doc = 'index'
project = 'pytest-cov'
year = '2010-2024'
author = 'pytest-cov contributors'
copyright = f'{year}, {author}'
version = release = '6.1.1'

pygments_style = 'trac'
templates_path = ['.']
extlinks = {
    'issue': ('https://github.com/pytest-dev/pytest-cov/issues/%s', '#'),
    'pr': ('https://github.com/pytest-dev/pytest-cov/pull/%s', 'PR #'),
}
html_theme = 'furo'
html_theme_options = {
    'githuburl': 'https://github.com/pytest-dev/pytest-cov/',
}

html_use_smartypants = True
html_last_updated_fmt = '%b %d, %Y'
html_split_index = False
html_short_title = f'{project}-{version}'

linkcheck_anchors_ignore_for_url = [
    r'^https?://(www\.)?github\.com/.*',
]

napoleon_use_ivar = True
napoleon_use_rtype = False
napoleon_use_param = False
