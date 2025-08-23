# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from pathlib import Path

# Add parent directories to sys.path for module discovery
project_root = Path(__file__).resolve().parents[3]
database_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(database_root))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Virtual Ontology Database'
copyright = '2025, Virtual Ontology Team'
author = 'Virtual Ontology Team'
release = '2.0.0'

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
    'sphinx_autodoc_typehints',      # Automatically document type hints
    'autoapi.extension',             # Automatic API documentation generation
]

# AutoAPI Configuration
autoapi_type = 'python'
autoapi_dirs = [
    str(database_root),              # Database module
    str(project_root / 'config'),    # Configuration module it depends on
]

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
    '*/test_*',
    '*/tests/*',
    '*.pyc',
    '*.pyo',
]

autoapi_keep_files = True
autoapi_add_toctree_entry = True
autoapi_root = 'api'  # Output generated API docs to api/ subdirectory

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
    'show-inheritance': True,
}

autodoc_typehints = 'description'
autodoc_typehints_format = 'short'
autodoc_mock_imports = []  # Add any external dependencies that aren't available at build time

# Intersphinx mapping for cross-references
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'sqlmodel': ('https://sqlmodel.tiangolo.com/', None),
    'fastapi': ('https://fastapi.tiangolo.com/', None),
    'pydantic': ('https://docs.pydantic.dev/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
}

# Templates and static files
templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_show_sourcelink = True
html_show_sphinx = True
html_show_copyright = True

# Theme options
html_theme_options = {
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
    'style_nav_header_background': '#2980B9',
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
}

# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '10pt',
    'preamble': '',
    'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files
latex_documents = [
    ('index', 'VirtualOntologyDatabase.tex', 'Virtual Ontology Database Documentation',
     'Virtual Ontology Team', 'manual'),
]

# -- Options for manual page output ------------------------------------------

man_pages = [
    ('index', 'virtualontologydatabase', 'Virtual Ontology Database Documentation',
     ['Virtual Ontology Team'], 1)
]

# -- Options for Texinfo output ----------------------------------------------

texinfo_documents = [
    ('index', 'VirtualOntologyDatabase', 'Virtual Ontology Database Documentation',
     'Virtual Ontology Team', 'VirtualOntologyDatabase', 
     'Database module for the Virtual Ontology system',
     'Miscellaneous'),
]

# -- Extension configuration -------------------------------------------------

# Todo extension
todo_include_todos = True

# Coverage extension
coverage_show_missing_items = True