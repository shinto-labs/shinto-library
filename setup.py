#!/usr/bin/env python3

from setuptools import setup

setup(
    name='shinto',
    version='1.0.1',
    description='Shinto Labs default python library',
    author='Tommy van Schie',
    author_email='tommy@shintolabs.nl',
    url='http://www.shintolabs.nl',
    packages=[
        'shinto'
    ],
    install_requires=[
        'pyyaml',
    ]
)
