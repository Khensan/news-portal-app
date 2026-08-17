import os
import sys
import django

# 1. Clear out any incorrect old environment variables
if 'DJANGO_SETTINGS_MODULE' in os.environ:
    del os.environ['DJANGO_SETTINGS_MODULE']

# 2. Add your absolute project root directory to the Python path safely
sys.path.insert(0, os.path.abspath('../../'))

# 3. Point Sphinx to your exact Django settings file location
os.environ['DJANGO_SETTINGS_MODULE'] = 'news_project.settings'

# 4. Safely initialize your Django model configurations
django.setup()


# Configuration file for the Sphinx documentation builder.
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'News Portal'
copyright = '2026, Khensani'
author = 'Khensani'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '.venv', '.venv-1', '.venv-2']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

# -- Custom handler to skip standard Django/Database fields in autodoc --------
def skip_django_internal_fields(app, what, name, obj, skip, options):
    # Hide dynamic model fields, tracking attributes, and manager objects
    django_fields = ['id', 'objects', 'DoesNotExist', 'MultipleObjectsReturned']
    if what == "class" and name in django_fields:
        return True
    return skip

def setup(app):
    app.connect("autodoc-skip-member", skip_django_internal_fields)
