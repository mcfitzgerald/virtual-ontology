# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from pathlib import Path

# Add parent directories to sys.path for module discovery
project_root = Path(__file__).resolve().parents[3]
twin_model_root = Path(__file__).resolve().parents[2]

# Add all required paths
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(twin_model_root))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Virtual Ontology Twin Model'
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
    str(twin_model_root),                    # Twin model module
    str(project_root / 'manifests'),         # Manifests it depends on
    str(project_root / 'ontology'),          # Ontology definitions
    str(project_root / 'config'),            # Configuration module
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
    '*/serve_docs.py',
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
autodoc_mock_imports = ['simpy']  # Mock SimPy if not available at build time

# Intersphinx mapping for cross-references
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'simpy': ('https://simpy.readthedocs.io/en/latest/', None),
    'pydantic': ('https://docs.pydantic.dev/', None),
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
    ('index', 'VirtualOntologyTwinModel.tex', 'Virtual Ontology Twin Model Documentation',
     'Virtual Ontology Team', 'manual'),
]

# -- Options for manual page output ------------------------------------------

man_pages = [
    ('index', 'virtualontologytwinmodel', 'Virtual Ontology Twin Model Documentation',
     ['Virtual Ontology Team'], 1)
]

# -- Options for Texinfo output ----------------------------------------------

texinfo_documents = [
    ('index', 'VirtualOntologyTwinModel', 'Virtual Ontology Twin Model Documentation',
     'Virtual Ontology Team', 'VirtualOntologyTwinModel', 
     'Ontology-driven simulation framework for virtual twins',
     'Miscellaneous'),
]

# -- Extension configuration -------------------------------------------------

# Todo extension
todo_include_todos = True

# Coverage extension
coverage_show_missing_items = True