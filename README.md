# Shinto Library

Library for shared config and connections for Shinto repositories

## Release

To release a tag run: `./release.sh` or `bash ./release.sh` on Windows.


## Tests
 Tests use Nose2 

### test prerequisits

Make a Python Virtual Env
`python3 -m venv test-env`

Access the virtual Env
`source test-env/bin/activate`

Install libraries needed for testing:
```
pip install nose2
python ./setup.py develop
```

### Run tests
(first access test-env: `source ./test-env/bin/activate`)

`./run-tests.sh`