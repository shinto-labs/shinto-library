#!/bin/bash

ruff check -v

# Run the nose2 tests in the ./tests directory
nose2 -v