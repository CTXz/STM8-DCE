# Tests

This directory contains tests for the stm8dce tool. Testing is divided into two main parts:

1. **test.py**: Contains unit tests to verify the functionality of the stm8dce tool. These tests use a set of tailored C files (`main.c`, `_main.c`, `extra.c` and `rel.c`) to test various features and ensure the tool behaves as expected. The unit tests validate the returned lists of excluded and kept functions and constants against predefined expected outputs.

2. **test_project**: A test project designed to evaluate if stm8dce works on a real project. This project is based on the ["Dampflog Interface Board Firmware"](https://github.com/TuDo-Makerspace/Dampflog). It aims to identify potential issues that may have slipped past the unit tests. The test project is only tested for successful compilation.

These tests are ran accross multiple SDCC version to ensure broader compatibility. Currently, the tests are run on the following SDCC versions:

- 3.8.0
- 3.9.0
- 4.0.0
- 4.1.0
- 4.2.0
- 4.3.0
- 4.4.0

Older versions than 3.8.0 are not tested since these are not available as precompiled binaries on the official SDCC website.

## Running the tests

### Full test

The full test is intended to be run in a Docker container. The root directory of the stm8dce repository provides a Dockerfile that runs the tests on all above listed SDCC versions. To build the Docker image, run the following command:

```bash
docker build -t stm8dce-test .
```

To run the tests, execute the following command:

```bash
docker run stm8dce-test
```

The Docker container will run the tests on all above listed SDCC versions and output the results to the console.

It is not recommended to run the full test outside of docker, as it will clutter your system with multiple SDCC versions and other test-relevant dependencies.

### Unit test only

For faster testing, it's recommended to run the unit tests for your installed SDCC version only. To do so, simply run the `test.py` script:

```bash
python3 test.py
```