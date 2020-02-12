# Testing LiteX Build Environment in Renode

LiteX Build Environment comes with a set of test suites
verifying if the firmware runs correctly.

The tests are written in Robot Framework
and are intended to be run using Renode simulator.

They are located in `tests/renode` directory.
Each `.robot` file targets a selected firmware.

The `scripts/test-renode.sh` script
is responsible for preparing the environment
and running the appropriate test suites
based on the current LiteX Build Environment
configuration.

## CI integration

Tests are run automatically in Travis CI.

## Running tests manually

In order to run tests locally execute
all the commands necessary to build the
firmware and then `scripts/test-renode.sh`, e.g.:

``` bash
$ export CPU=vexriscv; export PLATFORM=arty; export FIRMWARE=micropython
$ ./scripts/download-env.sh
...
$ . ./scripts/enter-env.sh
...
$ ./scripts/build-micropython.sh
...
$ ./scripts/test-renode.sh
```

This will generate Renode platform/script,
select robot test suite targeting MicroPython
and run the test.

## Tests results

In the output of `scripts/test-renode.sh` you should find the following lines:

```
Preparing suites
Starting suites
Running tests/renode/BIOS.robot
+++++ Starting test 'BIOS.BIOS boots'
+++++ Finished test 'BIOS.BIOS boots' in 1.38 seconds with status OK
Finished tests/renode/BIOS.robot in 3.936288833618164 seconds
Running tests/renode/Firmware-micropython.robot
+++++ Starting test 'Firmware-micropython.Print help and version'
+++++ Finished test 'Firmware-micropython.Print help and version' in 52.33 seconds with status OK
Finished tests/renode/Firmware-micropython.robot in 52.60649251937866 seconds
Cleaning up suites
Aggregating all robot results
Output:  build/conda/opt/renode/tests/tests/robot_output.xml
Log:     build/conda/opt/renode/tests/tests/log.html
Report:  build/conda/opt/renode/tests/tests/report.html
Tests finished successfully :)
```

As mentioned in the log, Robot Framework will generate
`robot_output.xml` with the details of the test execution
together with two human readable `html` files: `log` and `report`.

In case of test failure, the script will print the content
of the `robot_output.xml` file to the standard output.
You should grep for `FAIL` or inspect the `log.html` file.
