#!/bin/bash
set -e

# create venv
python3 -m venv .venv

# activate venv
source .venv/bin/activate

#update pip
pip install --upgrade pip

# install dependencies
pip install -r requirements.txt