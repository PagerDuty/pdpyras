#!/bin/bash

refresh_virtualenv () {
    echo "Re-creating temporary virtualenv"
    rm -rf ./tmp
    mkdir -p ./tmp
    virtualenv ./tmp >/dev/null 2>&1
}

echo "Uploading to test.pypi.org"
twine upload --repository-url https://test.pypi.org/legacy/ dist/*

refresh_virtualenv
source ./tmp/bin/activate
echo "Testing install from scratch"
pip install --index-url https://test.pypi.org/simple/ pdpyras
deactivate

refresh_virtualenv
source ./tmp/bin/activate
echo "Testing install and then upgrade"
pip install pdpyras
pip install --upgrade --index-url https://test.pypi.org/simple/ pdpyras
deactivate
rm -rf tmp
