#!/bin/bash

set -e
set -x

virtualenv .virtualenv

source .virtualenv/bin/activate

python setup.py develop

