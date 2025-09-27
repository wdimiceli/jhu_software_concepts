import os
import sys
sys.path.insert(0, os.path.abspath("../src"))

project = "Grad Café Analytics"
author = "Wesley DiMiceli"
release = "1.0.0"
version = "1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = []

# Theme options
html_theme_options = {
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# Autodoc options
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'flask': ('https://flask.palletsprojects.com/en/2.3.x/', None),
    'psycopg': ('https://www.psycopg.org/psycopg3/docs/', None),
}
