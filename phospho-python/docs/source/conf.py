# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys

# sys.path.insert(0, os.path.abspath("../.."))  # Source code dir relative to this file
from phospho import __version__

# -- Project information -----------------------------------------------------

project = "phospho"
copyright = "2023, phospho"
author = "phospho"
version = __version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "myst_parser",
    "autodoc2",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
]
autodoc2_packages = [
    "../../phospho",
]
autodoc2_docstring_parser_regexes = [
    (r"autodoc2\.sphinx\.docstring\._example", "myst"),
]
autodoc2_render_plugin = "myst"

# Put ignored modules for autodoc here:
autodoc2_skip_module_regexes = [
    r"phospho\.(agent|steps|_version|message)",
]

myst_enable_extensions = ["fieldlist", "deflist"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# Exclude the prompt "$" when copying code
copybutton_prompt_text = r"\$ "
copybutton_prompt_is_regexp = True

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_title = project
html_theme = "sphinx_book_theme"
html_logo = "assets/phospho-logo.png"
html_theme_options = {
    "logo_only": True,
    "path_to_docs": "docs/source",
    "repository_url": "https://github.com/phospho-app/phospho",
    "use_repository_button": True,
}
html_favicon = "assets/favicon.ico"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

autosummary_generate = True  # Turn on sphinx.ext.autosummary
