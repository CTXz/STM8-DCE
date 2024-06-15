#!/bin/bash

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd $DIR/src
pdoc --force --html --output-dir ../docs --config show_source_code=False stm8dce
echo "Documentation has been generated in the docs directory."
