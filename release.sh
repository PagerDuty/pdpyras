#!/bin/bash

ver=$1
[[ -z $ver ]] && echo "Please enter a version number." && exit 1

sed -i.bak "s/^__version__ = '[^']*'$/__version__ = '$ver'/g" pdpyras.py setup.py
vim CHANGELOG.rst
make docs
git add CHANGELOG.rst docs/
git commit -a -m "Version $ver"
git tag $ver
