"""Sphinx configuration for twin_model documentation."""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Project information
project = "Twin Model"
copyright = "2025, Virtual Ontology Team"
author = "Virtual Ontology Team"
release = "1.0.0"

# Extensions
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosummary",
    "autoapi.extension",
    "myst_parser",
    "sphinx_llms_txt",
]

# MyST-Parser configuration for Markdown support
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]

# Source file suffixes
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# Master document
master_doc = "index"

# Language
language = "en"

# Exclude patterns
exclude_patterns: list[str] = []

# HTML theme
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False,
    "sticky_navigation": True,
}

# Autodoc configuration
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
    "show-inheritance": True,
}

# Napoleon settings for Google-style docstrings
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

# Autosummary settings
autosummary_generate = True
autosummary_generate_overwrite = True

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "simpy": ("https://simpy.readthedocs.io/en/latest/", None),
}

# AutoAPI configuration
autoapi_type = "python"
autoapi_dirs = ["../../twin_model"]
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "imported-members",
]
autoapi_ignore = ["*/tests/*", "*/__pycache__/*"]
autoapi_keep_files = True
autoapi_add_toctree_entry = False

# Type hints configuration (removed as extension not available)
