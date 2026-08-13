import os
import sys
import django

# Add your project root directory to the Python path
sys.path.insert(0, os.path.abspath('..'))

# Point Sphinx to your Django settings file
os.environ['DJANGO_SETTINGS_MODULE'] = 'news_portal_app.settings'  # Update with your actual settings folder name
django.setup()


# Configuration file for the Sphinx documentation builder.
#
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

extensions = []

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
