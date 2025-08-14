# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to find the twin module
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Virtual Twin'
copyright = '2024, Virtual Twin Team'
author = 'Virtual Twin Team'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',           # Core autodoc functionality
    'sphinx.ext.napoleon',           # Support for NumPy and Google docstrings
    'sphinx.ext.viewcode',           # Add links to highlighted source code
    'sphinx.ext.intersphinx',        # Link to other project's documentation
    'sphinx.ext.todo',               # Support for todo items
    'sphinx.ext.coverage',           # Documentation coverage reports
    'sphinx.ext.mathjax',            # Render math via JavaScript
    'sphinx.ext.ifconfig',           # Include content based on configuration
    'sphinx.ext.githubpages',        # Create .nojekyll file for GitHub Pages
    'sphinx_autodoc_typehints',     # Automatically document type hints
    'autoapi.extension',            # Automatic API documentation generation
]

# AutoAPI Configuration
autoapi_type = 'python'
autoapi_dirs = ['../../twin']
autoapi_options = [
    'members',                  # Document members
    'undoc-members',           # Include members without docstrings
    'show-inheritance',        # Show inheritance relationships
    'show-module-summary',     # Add module summary
    'special-members',         # Document special members like __init__
    'imported-members',        # Document imported members
]
autoapi_ignore = [
    '*/__pycache__/*',
    '*/config/*',
    '*/configs/*',
]
autoapi_keep_files = True
autoapi_add_toctree_entry = True

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}
autodoc_typehints = 'description'
autodoc_typehints_format = 'short'
autodoc_mock_imports = []

# Intersphinx mapping for external documentation
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/', None),
    'pymoo': ('https://pymoo.org/', None),
}

# Templates path
templates_path = ['_templates']

# List of patterns to ignore when looking for source files
exclude_patterns = []

# The suffix(es) of source filenames
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# The master toctree document
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#2980B9',
    # Toc options
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

html_static_path = ['_static']
html_css_files = []
html_js_files = []

# Output file base name for HTML help builder
htmlhelp_basename = 'VirtualTwindoc'

# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '10pt',
    'preamble': '',
    'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files
latex_documents = [
    (master_doc, 'VirtualTwin.tex', 'Virtual Twin Documentation',
     'Virtual Twin Team', 'manual'),
]

# -- Options for manual page output ------------------------------------------

man_pages = [
    (master_doc, 'virtualtwin', 'Virtual Twin Documentation',
     [author], 1)
]

# -- Options for Texinfo output ----------------------------------------------

texinfo_documents = [
    (master_doc, 'VirtualTwin', 'Virtual Twin Documentation',
     author, 'VirtualTwin', 'Manufacturing Digital Twin Simulation & Optimization',
     'Miscellaneous'),
]

# -- Extension configuration -------------------------------------------------

# TODO extension
todo_include_todos = True

# Coverage extension
coverage_show_missing_items = True

# Suppress warnings
suppress_warnings = ['autoapi']