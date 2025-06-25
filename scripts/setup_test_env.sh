#!/bin/bash
# Setup environment for Daffodil tests similar to GitHub Actions
set -euo pipefail

# install system dependencies for psycopg3
sudo apt-get update
sudo apt-get install -y libpq-dev

# install python dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install .

# run the test suite
python test/tests.py
