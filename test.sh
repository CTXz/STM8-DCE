#!/bin/bash

# Copyright (C) 2024 Patrick Pedersen

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Description: This script runs the unit tests for each SDCC version specified in the SDCC_VERSIONS array.

# NOTE: This script is launched by the dockerfile of the project. Since this script relies on the SDCC binaries
#       being installed in the /opt directory, it is recommended to run this script as intended by the dockerfile.
#       To do so, simply run the following command:
#       docker build -t stm8dce-test . && docker run stm8dce-test 

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Tested SDCC versions (These are available as pre-built binaries)
SDCC_VERSIONS=("3.8.0" "3.9.0" "4.0.0" "4.1.0" "4.2.0" "4.3.0" "4.4.0")

PASSED_VERSIONS=()
FAILED_VERSIONS=()

# Escape codes for colored output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Run unit tests for each SDCC version
for version in "${SDCC_VERSIONS[@]}"; do
    export PATH="/opt/sdcc-$version/bin:$PATH"
    
    echo "Running test.py with SDCC version $version"
    if python3 $SCRIPT_DIR/test/test.py $SCRIPT_DIR/test/build-$version; then
        PASSED_VERSIONS+=("$version")
    else
        FAILED_VERSIONS+=("$version")
    fi
done

# Print summary
echo
echo "Summary:"
echo "=============================="
if [ ${#PASSED_VERSIONS[@]} -ne 0 ]; then
    echo -e "Passed:"
    for version in "${PASSED_VERSIONS[@]}"; do
        echo -e "  - ${GREEN}SDCC version $version${NC}"
    done
else
    echo -e "Passed: None"
fi

if [ ${#FAILED_VERSIONS[@]} -ne 0 ]; then
    echo -e "Failed:"
    for version in "${FAILED_VERSIONS[@]}"; do
        echo -e "  - ${RED}SDCC version $version${NC}"
    done
else
    echo -e "Failed: None"
fi