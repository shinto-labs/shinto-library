#!/usr/bin/env python3

"""Setup file for the shinto package."""

from setuptools import setup

setup(
    name="shinto",
    version="1.0.3",
    description="Shinto Labs default python library",
    author="Tommy van Schie",
    author_email="tommy@shintolabs.nl",
    maintainer="Shinto Labs BV",
    maintainer_email="info@shintolabs.nl",
    url="http://www.shintolabs.nl",
    packages=["shinto"],
    install_requires=["pyyaml==6.0.1", "jsonschema==4.23.0", "prometheus_client"],
    extras_require={
        "database": ["psycopg[pool]==3.2.1"],
        "uvicorn": ["uvicorn==0.30.1"],
        "all": ["psycopg[pool]==3.2.1", "uvicorn==0.30.1"],
    },
    python_requires=">=3.10",
)
