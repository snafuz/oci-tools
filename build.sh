#!/bin/bash

if ! bumpversion --commit patch
then
    echo ''
    echo '========================================='
    echo 'Unable to update the version.'
    echo 'Did you run git add . && git commit ?'
    echo '========================================='
    echo ''
    exit 1
fi

python setup.py sdist
VERSION=`sed -n -e '/__version__/ s/.*\= *//p' oci_tools/__init__.py | sed -e "s/^'//" -e "s/'.*$//"`
git tag rel-$VERSION
