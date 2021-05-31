# FlakyReporter

A package used for re-running known flaky tests and producing a report on if they could be flaky due to Randomness.

## Installation

Requires installation of ```pytest-trace```, locate inside the ```pytest-trace/``` folder.
Firstly install ```pytest-trace``` by running ```pip install pytest-trace/pytest-trace```.

FlakyReporter is installed by running ```pip install flakyreporter```.

## Usage

__READ IMPORTANT USAGE BEFORE RUNNING THE APPLICATION__

When both ```pytest-trace``` and ```flakyreporter``` are installed the program can be used as a python3 package.

The most common type of command to execute is:
```python3 -m flakyreporter -i 100 -f ./someproject/tests/test.py -t test_testFunctionName```
This command will run the file ```test.py``` 100 times and trace the execution of ```test_testFunctionName``` and then produce a report for it.

If you already have valid log files stored, you can scan them directly by running:
```python3 -m flakyreporter --scan -t test_testFunctionName```
which will scan the trace logs from the ```test_testFunctionName``` function and produce a report on the findings made.

### Important Usage

The ```pytest.ini``` file must be located inside the target project folder and the ```__pycache__`` folder created from the tests run must be removed before the FlakyReporter will fully work.

### Flags

| Flag                | Description                                                                                                                                                                                                                                                                                                                                                                                                                                            | Usage                      |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------|
| --scan              | Scans the trace logs with the given name by the -t flag                                                                                                                                                                                                                                                                                                                                                                                                | ```--scan```               |
| -t<br/>--target     | Sets the target(s) to be traced or scanned.<br/> Must include at minimum 1 argument.<br/> Can include more than one test as described in usage.                                                                                                                                                                                                                                                                                                        | ```-t test_a test_b ...``` |
| --reset             | If this flag is set it will delete the ```tracelogs/``` folder and all its content.                                                                                                                                                                                                                                                                                                                                                                    | ```--reset```              |
| -i<br/>--iterations   | Sets the number of iterations to rerun the target file for scanning.                                                                                                                                                                                                                                                                                                                                                                                   | ```-i 100```               |
| -f<br/>--file       | Specifies the target folder or file where either all test files lay or where the target test file is located. <br/>   Can be given ```-f all```as flag and it will run all test files located from the  current "root".<br/>  If given a test file, such as ```-f tests/test.py``` it will only run the ```test.py``` file. <br/>  If given a folder, such as ```-f tests```it will run the entire test suite located in the ```tests/``` folder.<br/> | ```-f tests/test.py```     |
