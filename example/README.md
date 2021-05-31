# Example Trace Logs

In this folder two example trace logs are located. The passed runs of trace logs are locate in the passed folder and the failed runs in the failed folder. 

Note that this example run does not require any ```pytest.ini```.

The example functions are:
 - test_AveragedFunction
 - test_valid_api_forum

To run and produce a report on these files, stand in this *example* folder with the terminal and execute the command <br/>
```python3 -m flakyreporter --scan -t test_AveragedFunction test_valid_api_forum```

Note that the scanning requires the *tracelogs/* folder to be in the active working directory (i.e. *"./tracelogs"*).
