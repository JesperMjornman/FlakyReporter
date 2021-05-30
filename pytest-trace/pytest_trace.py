import pytest, sys, traceback, linecache, inspect, json, collections, os
from flakyreporter.loghandler import LogHandler

def pytest_addoption(parser):
    group = parser.getgroup('flakytrace')
    group.addoption(
        '--flakytrace',
        action='store_true',
        dest='counter',
        default=False,
        help='enable tracing for FlakyReporter'
    )
try: 
    to_trace = [line.rstrip() for line in open('./tracelist.lst')]
except:
    to_trace = []
print(to_trace)
logger = LogHandler()
def _trace_lines(frame, event, arg):  
    """
    Function used for tracing executed lines.
    Inserts into log: lineno : Tuple[line_str, locals]
    """
    global logger
    co = frame.f_code
    parent = frame.f_back.f_code
    func_name = co.co_name  

    if event == 'line':
        if func_name.split('::')[-1] in to_trace:
            logger.log_trace(frame, event, arg)
        elif parent.co_name in to_trace:
            logger.log_trace(frame, event, arg, True)

    elif parent.co_name.split('::')[-1] in to_trace and (event == 'call' or event == 'return'):
        if '/usr/lib/' in co.co_filename \
          or '_pytest' in co.co_filename \
          or 'Python/Python/' in co.co_filename \
          or 'Python\\Python' in co.co_filename:
            return
        logger.log_trace(frame, event, arg)
    return _trace_lines

@pytest.hookimpl
def pytest_runtest_call(item):
    """
    Hooks pytest oncall function.
    Runs when a test is called.

    Args:
        item - pytest item (provided by pytest)
    """
    if item.name in to_trace:
        global logger
        logger.logs[item.name] = {
            'lines' : dict()
        }
        sys.settrace(_trace_lines)

@pytest.hookimpl
def pytest_runtest_teardown(item, nextitem):    
    sys.settrace(None)

@pytest.hookimpl    
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Hooks writing summary to terminal from pytest.
    This enables us to catch explanation on why the assert failed.
    """
    for report in terminalreporter.getreports("failed"):
        try:
            report_json = report._to_json()
            func_name = report_json['nodeid'].split("::")[1]
            if func_name in to_trace: 
                logger.log_pytest_fail(func_name, report_json)                  
        except Exception as e:
            print(e)
    _print_logs()

@pytest.hookimpl
def pytest_assertion_pass(item, lineno, orig, expl):
    """
    Experimental hook from pytest.
    Hooks passing assertments giving the content to why it passed.
    """
    if item.name in to_trace:
        logger.log_pytest_pass(item, lineno, orig, expl)

def _print_logs():
    """
    Writes the logs to their respective files into either tracelogs/passed or tracelogs/failed.
    """
    global logger
    logger.save_logs()    
   # print(logger.dump_logs())