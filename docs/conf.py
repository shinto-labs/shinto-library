"""Configuration file for the Sphinx documentation builder."""  # noqa: INP001

import re
import sys
from pathlib import Path

sys.path.insert(0, Path(__file__).resolve().parents[1])

project = "Shinto"
copyright = "2024, Shinto Labs"  # noqa: A001
author = "Aron Hemmes"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# Read the version from pyproject.toml
with Path("../pyproject.toml").open("r") as f:
    content = f.read()

match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
release_version = match.group(1)

rst_epilog = f"""
.. |release| replace:: git+ssh://git@github.com/shinto-labs/shinto-library.git@v{release_version}
"""
