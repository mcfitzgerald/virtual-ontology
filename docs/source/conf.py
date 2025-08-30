"""Configuration file for the Sphinx documentation builder."""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Project information
project = 'Virtual Twin Model'
copyright = '2024, Virtual Ontology Team'
author = 'Virtual Ontology Team'
release = '1.0.0'

# Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'sphinx.ext.intersphinx',
    'autoapi.extension',
    'myst_parser',
]

# AutoAPI Configuration
autoapi_dirs = [str(root_dir / 'twin_model')]
autoapi_type = 'python'
autoapi_options = [
    'members',
    'undoc-members',
    'show-inheritance',
    'show-module-summary',
    'imported-members',
    'special-members',
]
autoapi_ignore = [
    '*/tests/*',
    '*/test_*.py',
    '*/__pycache__/*',
]
autoapi_keep_files = True
autoapi_root = 'api'
autoapi_add_toctree_entry = True
autoapi_member_order = 'groupwise'
autoapi_python_class_content = 'both'
autoapi_template_dir = str(Path(__file__).parent.parent / 'templates')

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
    'show-inheritance': True,
}
autodoc_typehints = 'both'
autodoc_typehints_format = 'short'
autodoc_typehints_description_target = 'documented'

# MyST Parser for Markdown support
myst_enable_extensions = [
    'deflist',
    'tasklist',
    'html_image',
    'colon_fence',
    'smartquotes',
    'replacements',
    'linkify',
    'strikethrough',
]
myst_heading_anchors = 3

# Source file parsers
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# Master document
master_doc = 'index'

# Templates
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# HTML output
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
}

# LaTeX output
latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '10pt',
    'preamble': '',
    'figure_align': 'htbp',
}

# Intersphinx mapping (for linking to external documentation)
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'simpy': ('https://simpy.readthedocs.io/en/latest/', None),
    'pydantic': ('https://docs.pydantic.dev/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
}

# Todo extension settings
todo_include_todos = True

# Output formats for documentation
# This will be used by custom builders for LLM-friendly output
llm_output_format = 'markdown'
llm_output_dir = str(root_dir / 'docs' / 'llm_output')