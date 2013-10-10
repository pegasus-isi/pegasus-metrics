#!/bin/bash

set -e
set -x

source .virtualenv/bin/activate

python setup.py test

