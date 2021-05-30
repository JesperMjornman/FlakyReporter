from flakyreporter.util import bcolors as Color
import sys, inspect, collections, os, traceback, linecache
import json, pytest, platform, datetime, threading, re, glob
class LogHandler():
    """
    Represents a logging object that handles logging the tracing and test results.
    """
    def __init__(self, meta = None):
        self.logs = self._init_log_structure()
        self.err  = None
        self.t_lock = threading.Lock()
        self.iteration_info = dict()
        
    def read_logs(self, targets):
        """
        Read all logs from ./tracelogs folder.
        Note that each log is of different format in comparison to the writing of logs.

        Each log is now differentiated by self.logs[func_name][passed/failed][iteration].
        This allows for comparisons between several logs.
        """
        self.logs = dict()
        self.log_meta(None, True)
    
        t_passing = threading.Thread(target = self._async_read_log, args=('passed', targets, ))
        t_failing = threading.Thread(target = self._async_read_log, args=('failed', targets, ))

        t_passing.start()
        t_failing.start()

        t_passing.join()
        t_failing.join()

        if self.err:
            raise Exception(self.err)
          
    def log_meta(self, meta, load_cpu_info = True)->None:
        if meta is not None:
            self.logs['meta'] = meta
        else:
            if load_cpu_info:
                try:
                    from cpuinfo import get_cpu_info
                    cpu = get_cpu_info()['brand']
                except:
                    cpu = platform.processor()
            else:
                cpu = platform.processor()

            self.logs['meta'] = { 
                'OS' : {
                    'platform'  : platform.platform().__str__(),           
                    'system'    : platform.system().__str__(),
                    'release'   : platform.release().__str__(),
                    'version'   : platform.version().__str__(),
                    'machine'   : platform.machine().__str__(),
                    'processor' : cpu,
                    'pyversion' : sys.version
                },
                'DATE'  : datetime.datetime.now().strftime("%Y-%d-%m %H:%M:%S")
            }

    def dump_logs(self)->str:
        """
        Dumps logs
        """
        return json.dumps(self.logs, indent=4)

    def dump_meta(self)->str:
        """
        Dumps meta information
        """
        return json.dumps(self.logs['meta'], indent=4)

    def log_time(self, func_name, t_type, s = None, e = None)->None:
        start = ''
        end   = ''
        if t_type == 'start':
            start = datetime.datetime.now().strftime("%H:%M:%S:%f")
        elif t_type == 'end':
            end = datetime.datetime.now().strftime("%H:%M:%S:%f")
        elif t_type == None:
            start = s
            end = e

        if func_name not in self.logs:
            self.logs[func_name] = dict()

        self.logs[func_name]['time'] = {
            'start' : start,
            'end'   : end
        }

    def save_logs(self)->None:
        """
        Store all logs in the ./tracelogs folder
        """
        for k, v in self.logs.items():
            self.write_log(k)
        

    def log_pytest_fail(self, func_name, report_json):
        """
        Logs failed pytest summary.
        """
        self._log_function_def(func_name)
        try:              
            self.logs[func_name]['result'] = {
                'res'  : 'failed',
                'line' : report_json['longrepr']['reprcrash']['lineno'],
                'expl' : report_json['longrepr']['reprcrash']['message']
            }
        except Exception as e:
            print(e)
        
    def log_pytest_pass(self, item, lineno, orig, expl):
        """
        Logs passed pytest summary.
        """
        self._log_function_def(item.name)
        if item.name in self.logs:
            self.logs[item.name]['result'] = {
                'res'  : 'passed',
                'line' : lineno,
                'expl' : expl
            }

    def log_trace(self, frame, event, arg, call = False):
        """
        Logs the current trace.
        """
        co = frame.f_code
        parent    = frame.f_back.f_code
        filename  = co.co_filename
        func_name = co.co_name  
        line_no   = frame.f_lineno
        f_locals  = frame.f_locals

        if event == 'line':
            if not call:
                try:
                    if func_name not in self.logs:
                        self.logs[func_name] = {
                            'lines' : dict(),
                            'call'  : dict()
                        }

                    if 'filename' not in self.logs[func_name]:
                        self.logs[func_name]['filename'] = filename
                    
                    self.logs[func_name]['lines'][line_no] = {
                        'str'    : str(linecache.getline(filename, line_no).rstrip()),
                        'locals' : str(f_locals)
                    } 
                except Exception as e:
                    print('Trace line exception, {}\nin file'.format(e, filename))
            else:
                try:
                    self.logs[parent.co_name]['call'][frame.f_back.f_lineno][func_name]['lines'][line_no] = {
                        'str'    : str(linecache.getline(filename, line_no).rstrip()),
                        'locals' : str(f_locals)
                    } 
                except Exception as e:
                    print('Trace line exception, {}\nin file {}'.format(e, filename))

        elif event == 'call':
            try:
                if parent.co_name in self.logs:   
                    if 'call' not in self.logs[parent.co_name]:
                        self.logs[parent.co_name]['call'] = dict()

                    if func_name not in self.logs[parent.co_name]['call']:
                        self.logs[parent.co_name]['call'][frame.f_back.f_lineno] = {
                            func_name : dict()             
                        }
                    
                    self.logs[parent.co_name]['call'][frame.f_back.f_lineno][func_name] = {                                 
                        'lines'    : dict(),
                        'filename' : filename,
                        'return'   : None
                    }
                    self.logs[parent.co_name]['call'][frame.f_back.f_lineno][func_name]['lines'][line_no] = {
                        'str' : str(linecache.getline(filename, line_no).rstrip())
                    }
            except Exception as e:
                print('Trace call exception, {}\nin file {}'.format(e, filename))

        elif event == 'return':
            try:
                if parent.co_name in self.logs:   
                    self.logs[parent.co_name]['call'][frame.f_back.f_lineno][func_name]['return'] = arg                               
            except Exception as e:
                print('Trace return exception, {}\nin file {}'.format(e, filename))
        


    def write_log(self, func_name):
        """
        Writes a log to its respective folder.
        """
        log = self.logs[func_name]
        try:
            f = open("./tracelogs/{}/{}.txt".format(log['result']['res'], func_name), "a+")      
            for k, v in collections.OrderedDict(sorted(log['lines'].items())).items():
                f.write("___line {} {}\n".format(k, v['str']))
                
                if 'call' in log and k in log['call']:
                    f.write(self._get_call(log['call'][k])) # Add C-> locals

                if 'result' in log and log['result']['line'] == k:
                    f.write(">\t({})\n".format(log['result']['expl']))
                else:
                    f.write(self._get_locals(log['lines'], k))        
                                
        except Exception as e:
            print('Writing log failed, {}'.format(e))
       
        try:
            f.write("{}\n\n".format("="*20))
            f.close()
        except:
            pass

    def _get_locals(self, trace, lineno)->str:
        """
        Places locals fetched from sys below the correct line.
        If a line contains a variable assigned a value the value of the variable will be printed below it 

        Args:
            func_name - function name
            lineno    - line number 

        Returns
            string containing that line's locals
        """
        if lineno + 1 not in trace \
            or trace[lineno + 1]['locals'] == "{{}}":
            return ''

        result = ''
        try:
            iterator = self._cast_json(trace[lineno + 1]['locals'])
            line = trace[lineno]['str']
            for k, v in iterator.items():
                if k in line:
                    result += "<\t({} = {})\n".format(k, v)
        except Exception as e:
            print('Locals Failed: {}'.format(e))
        return result

    def _get_call(self, log)->str:
        """
        Get a string representation of the currently called function

        Args:
            log - log of called function

        Returns:
            string representation of trace
        """
        result = ''
        try:
            for k, v in log.items():
                result += 'Call-> {} : {}\n'.format(k, v['filename'])
                for lineno, line in v['lines'].items():                                   
                    result += "C->\t\t___line {} {}\n".format(lineno, line['str'])      
                    
                    local_vars = self._get_locals(v['lines'], lineno)
                    if local_vars != '':
                        result += "C->\t{}".format(local_vars)
                    if 'return' in line['str']:
                        result += "C->\t\tret {}\n".format(v['return'])
        except Exception as e:
            print('Get call trace failed, {}'.format(e))

        return result

    def _cast_json(self, local_vars)->dict:
        """
        Converts the system locals to a dictionary object.
        Used as the convertion directly to json cast an exception.

        Args:
            local_vars - string of locals fetched from sys

        Returns:
            dictionary object containing all locals from string.
        """
        result = dict()
        try:
            formatted = local_vars.strip("{ }").replace(" ", "").replace("\'", "")
            formatted = formatted.split(",")
            for pair in formatted:
                keyval = pair.split(":")
                result[keyval[0]] = keyval[1]
        except IndexError:
            pass
        except Exception as e:
            print('Failed to cast to json, {}'.format(e))
        
        return result

    def _log_function_def(self, func_name)->None:
        """
        Logs the function line which is skipped from the tracing due to it not being a "line" event.

        Args:
            func_name - function name
        """
        try:
            line_no = min(self.logs[func_name]['lines'], key=int) - 1 
            self.logs[func_name]['lines'][line_no] = {
                "str"    : linecache.getline(self.logs[func_name]['filename'], line_no).rstrip().__str__(),
                "locals" : '{{}}'
            }
        except Exception as e:
            print('Failed log function definition: {}'.format(e))

    def _read_locals(self, line_split, start_index):
        line_split[start_index]  = line_split[start_index].strip("(")
        line_split[-1] = line_split[-1].replace(")\n", "")
        kvpair = ''.join(line_split[start_index:]).split("=")

        return kvpair

    def _read_init_dict(self, func_name, result, iteration):
        """
        Init dictionary for reading logs.
        """
        if iteration not in self.logs[func_name][result]:
            self.t_lock.acquire()                           
            self.logs[func_name][result][iteration] = {
                "lines" : dict(),                        
                "result" : {
                    "lineno" : -1,
                    "expl"   : ""   
                }
            }
            self.t_lock.release()

        if 'call' not in self.logs[func_name][result][iteration]:
            self.t_lock.acquire() 
            self.logs[func_name][result][iteration]['call'] = dict()
            self.t_lock.release()

    def _read_locals_(self, line, entry):
        """
        Read the locals of a given line.

        Args:
            line_split - list containing all words of a line
            entry      - parsed event containing `event_name, idx, entry]`
        """
        try:
            if entry[1] == 9:
                self.logs\
                    [entry[2]]\
                    [entry[3]]\
                    [entry[4]]\
                    [entry[5]]\
                    [entry[6]]\
                    [entry[7]]\
                    [entry[8]]\
                    [entry[9]]\
                    [entry[10]] += line
            elif entry[1] == 6:
                self.logs\
                    [entry[2]]\
                    [entry[3]]\
                    [entry[4]]\
                    [entry[5]]\
                    [entry[6]]\
                    [entry[7]] += line
        except Exception as e:
            print(self.logs)
            print('Reading locals failed, \"%s\"' % e)

    def _read_returns(self, line, entry):
        """
        Read the return statement of calls.

        Args:
            line_split - list containing all words of a line
            entry      - parsed event containing `[event_name, entry]`
        """
        try:
            self.logs\
                [entry[2]]\
                [entry[3]]\
                [entry[4]]\
                [entry[5]]\
                [entry[6]]\
                [entry[7]]\
                [entry[8]] += line
        except Exception as e:
            print('Reading return failed, \"%s\"' % e)

    def _async_read_log(self, result, targets)->None:
        """
        Read a log file.
        Is called by read_logs() using this function as async.

        Args:
            result - string representing if 'passing' or 'failing'
        """       
        for filename in os.listdir('{}/tracelogs/{}/'.format(os.getcwd(), result)):
            iteration = 0
            if targets is not None and filename[:-4] not in targets:
                continue
            with open(os.path.join('{}/tracelogs/{}/'.format(os.getcwd(), result), filename), 'r') as f:
                func_name = filename.split(".")[0]
                if func_name not in self.iteration_info:
                    self.iteration_info[func_name] = dict()

                self.t_lock.acquire() 
                if func_name not in self.logs:
                    self.logs[func_name] = dict()
                self.logs[func_name][result] =  {
                        iteration : {
                            "lines"  : dict(),                        
                            "result" : {
                                "lineno" : -1,
                                "expl"   : ""   
                            }
                        }
                    }
                self.t_lock.release()
                
                try:
                    lines = f.readlines()
                except UnicodeDecodeError:
                    self.err = (Color.FAIL + 'Unsupported Unicode format.' + Color.ENDC)
                    return
                
                lineno      = 0 
                call_lineno = 0               
                expl        = False
                call_name   = ''
                event       = None
                for line in lines:
                    try:
                        if iteration not in self.logs[func_name][result]:
                            self.t_lock.acquire()                           
                            self.logs[func_name][result][iteration] = {
                                "lines" : dict(),                        
                                "result" : {
                                    "lineno" : -1,
                                    "expl"   : "",
                                    "str"    : ""  
                                }
                            }
                            self.t_lock.release()

                        if 'call' not in self.logs[func_name][result][iteration]:
                            self.t_lock.acquire() 
                            self.logs[func_name][result][iteration]['call'] = dict()
                            self.t_lock.release()

                        line_split = [x for x in (line.replace("\t", " ").split(" ")) if x != '' and x != '\"']  
                        if line_split[0] == '___line': 
                            event    = None                       
                            lineno   = int(line_split[1])
                            if lineno < 0:
                                continue
                            
                            line_str = ' '.join(line_split[2:])
                           
                            self.logs[func_name][result][iteration]['lines'][lineno] = {
                                "str"    : line_str,
                                "locals" : ""
                            }
                        elif line_split[0] == 'Call->':
                            event = None
                            call_name = line_split[1]
                            self.logs[func_name][result][iteration]['call'][lineno] = dict()
                            self.logs[func_name][result][iteration]['call'][lineno][call_name] = {
                                'lines'    : dict(),
                                'filename' : line_split[3].rstrip("\n"),
                                'return'   : ""
                            }
                        elif line_split[0] == 'C->':
                            event = None
                            if line_split[1] == 'ret':
                                event = [2, -1, func_name, result, iteration, 'call', lineno, call_name, 'return']
                                self._read_returns(
                                    ' '.join(line_split[2:]).replace("\n", ""),
                                    event
                                )
                            elif line_split[1] == '<':            
                                event = [2, 9, func_name, result, iteration, 'call', lineno, call_name, 'lines', call_lineno, 'locals']  
                                self._read_locals_(
                                    ' '.join(line_split[2:]).replace("\n", "").replace("=", ":"),
                                    event
                                )
                            else:
                                call_lineno = int(line_split[2])
                                if call_lineno not in self.logs[func_name][result][iteration]['call'][lineno][call_name]['lines']:
                                    self.logs[func_name][result][iteration]['call'][lineno][call_name]['lines'][call_lineno] = {
                                        "str"    : "",
                                        "locals" : ""
                                    }

                                self.logs[func_name][result][iteration]['call'][lineno][call_name]['lines'][call_lineno]['str'] = ' '.join(line_split[3:]).rstrip("\n")                      
                        elif line_split[0] == "<": 
                            event = [1, 6, func_name, result, iteration, 'lines', lineno, "locals"]      
                            self._read_locals_(
                                ' '.join(line_split[1:]).replace("\n", "").replace("=", ":"),
                                event
                            )                                                    
                        elif line_split[0] == ">":
                            event = None
                            expl  = True
                            self.logs[func_name][result][iteration]['result'] = {
                                "lineno" : lineno,
                                "expl"   : ' '.join(line_split[1:]).rstrip("\n"),
                                "str"    : self.logs[func_name][result][iteration]['lines'][lineno]['str']
                            }                                           
                        elif event is not None:
                            if event[1] == -1:
                                self._read_returns(
                                    line,
                                    event
                                )
                            else:
                                self._read_locals_(
                                    line,
                                    event
                                )
                        elif line.replace("\n", "") == '====================':
                            iteration += 1
                            expl  = False
                            event = None    
                        elif expl:
                            self.logs[func_name][result][iteration]['result']['expl'] += line                  
                    except Exception as e:
                        self.err = ('Reading logs exception, \"%s\"' % e)
                        return

            self.t_lock.acquire()
            self.iteration_info[func_name][result] = iteration
            self.t_lock.release()

    def _init_log_structure(self)->dict:
        structure = dict()
        return structure
