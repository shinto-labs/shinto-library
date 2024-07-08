#!/usr/bin/env python3
"""Setup file for the shinto package."""

from setuptools import setup

setup(
    name="shinto",
    version="1.0.3",
    description="Shinto Labs default python library",
    author="Tommy van Schie",
    author_email="tommy@shintolabs.nl",
    url="http://www.shintolabs.nl",
    packages=["shinto"],
    install_requires=["pyyaml", "psycopg[pool]", "jsonschema"],
)
