import math, json
from util import RandReporterException
from util import bcolors as Color
from typing import ClassVar
from htmlformatter import HtmlFormatter

class RandomnessDetector:
    def __init__(self, logs, iteration_info, args_reset):
        self.logs = logs   
        self.rnd_probability  = 0
        self.equal_coverage   = False
        self.suspicious_vars  = {}
        self.ts_iterations    = None
        self.args_reset       = args_reset

        self.divergence = dict()    
        self.keywords   = dict()
        self.locals     = None
        self.returns    = { 'passed' : dict(), 'failed' : dict() }
        self.assertions = { 'passed' : dict(), 'failed' : dict() }
        self.collected_information = dict()
    
    def get_divergence(self, func_name):
        """
        Retrieves the differing lines of execution between passing and failing runs.
        If any divergence in execution is found, the method of analyzing must be altered 
        and/or conclude that it is impossible to, with accuracy, determine if the flakiness is due to randomness or not.

        Locates the first differing line between a passing and failing log. This is done for all logs meaning we compare
        all failing logs with all passing logs to find any divergence. If differing lines of execution are found they
        are stored inside the "result" variable and the execution continues with comparing logs. 

        No divergence hints that differing variables and return values between iterations are created by some form of randomness and
        any such findings are therefore more reliable when no divergence is found. Both failing/passing assertions and failing/passing function
        call return values are traced and stored. These will in turn help indicate locations that contain randomness.
        It further provides more data pertaining to found divergence; if a divergence is found, no further lines are analyzed. b
        By instead continually analyzing locals and return values we gain an indication (in a similar fashion as if no divergence was found).

        The locals and potential keywords are stored and returned. These are fetched, or located, for each line of commonly executed code.
        This means that if a divergence is found in the executed lines, all locals and keywords until that line are stored and further used to 
        possibly identify the reason of the divergence.

        If the resulting divergence is found to be present in more than one location, where the commons greatly differs, it is in turn difficult to further
        determine randomness as flakiness. 

        NOTE
            * Assumes all passing tests are equal in lines of execution.
            * For accurate information gathered, 2 failing logs (at minimum) should be created. 
            * Speed is not the aim of this application and an abundant amount of logs will slow down execution speed.

        Args:
            func_name - target test function name
        """
        
        if func_name not in self.logs\
         or 'failed' not in self.logs[func_name]\
         or 'passed' not in self.logs[func_name]:
            return {}
        
        self.locals       = { 'passed' : { func_name : dict() }, 'failed' : { func_name : dict() } }           
        divergent_lineno  = [-1, -1]
        found_divergence  = False

        for failed, failed_log in self.logs[func_name]['failed'].items():
            for passed, passed_log in self.logs[func_name]['passed'].items():
                commons = {
                    'testf' : dict(),
                    'calls' : dict()
                }
                for lineno, line in failed_log['lines'].items():
                    try:
                        # Store locals of current line
                        self._store_locals('passed', func_name, passed_log, lineno)
                        self._store_locals('failed', func_name, failed_log, lineno)

                        # Check for Divergence
                        if lineno == divergent_lineno[0] or line['str'] != passed_log['lines'][lineno]['str']:
                            self.divergence[lineno] = { 
                                func_name : { 
                                    'commons'  : commons,
                                    'expected' : passed_log['lines'][lineno]['str'], 
                                    'got'      : line['str'] } }

                            # Divergence is found, set new breakpoint and go to next iteration
                            divergent_lineno[0] = lineno
                            break
                    except:
                        pass                       
                    
                    # Check keywords, store common lines
                    self._check_for_keyword(func_name, lineno, line['str'])
                    commons['testf'][lineno] = line['str']
                    
                    # Check for Divergence in a called function.
                    # Same method as above.
                    try:
                        if failed_log['call'][lineno]:
                            for func, called in failed_log['call'][lineno].items():
                                for clineno, cline in called['lines'].items(): 
                                    if clineno == divergent_lineno[1] or cline['str'] != passed_log['call'][lineno][func]['lines'][clineno]['str']:
                                        self.divergence[lineno] = { 
                                            func : { 
                                                'clineno'  : clineno, 
                                                'commons'  : commons,
                                                'expected' : passed_log['call'][lineno][func]['lines'][clineno]['str'], 
                                                'got'      : cline['str'] 
                                            } 
                                        }
                                       
                                        divergent_lineno[1] = clineno
                                        break
                                    else:
                                        try:
                                            commons['calls'][func][clineno] = cline['str']
                                        except:
                                            commons['calls'][func] = dict()
                                            commons['calls'][func][clineno] = cline['str']

                                        self._check_for_keyword(func, clineno, cline['str'])
                            
                            self._store_returns(
                                func, 
                                lineno, 
                                passed_log['call'][lineno][func]['return'],
                                failed_log['call'][lineno][func]['return']
                            )  
                    except Exception as e:
                        pass
                
                try:
                    if passed_log['lines']:
                        final_line = list(passed_log['lines'].keys())[-1]
                        if final_line != lineno:
                            self.divergence[lineno] = { 
                                func_name : { 
                                    'clineno'  : clineno, 
                                    'commons'  : commons,
                                    'expected' : self.logs[func_name]['passed'][0]['lines'][final_line]['str'], 
                                    'got'      : ''
                                } 
                            } 
                except:
                    pass
                
                try:
                    self._store_assertions('passed', passed_log['result']['expl'], passed_log['result']['str'])
                except:        
                    pass
            try:
                self._store_assertions('failed', failed_log['result']['expl'], failed_log['result']['str'])
            except:
                pass

    def _store_assertions(self, result, expl, _str):
        if ("at0x" in expl or "at 0x" in expl)\
          or ("at0x" in _str or "at 0x" in _str):
            try:
                self.assertions[result]['trace']['lambda'] += 1
            except:
                self.assertions[result]['trace'] = dict()  
                self.assertions[result]['trace']['lambda'] = 1                 
        else:
            try:
                if expl != '':
                    self.assertions[result]['trace'][expl] += 1     
            except:      
                if 'str' not in self.assertions[result]:
                    self.assertions[result]['trace'] = dict()       
                self.assertions[result]['trace'][expl] = 1 
            try:   
                if expl != '':
                    self.assertions[result]['str'][_str] += 1
            except:
                if 'str' not in self.assertions[result]:
                    self.assertions[result]['str'] = dict()
                self.assertions[result]['str'][_str] = 1


    def _store_locals(self, key, func_name, log, lineno): # Fix
        if lineno not in log['lines']:
            return                         
        
        local = self._locals_to_json(log['lines'][lineno]['locals'])
        
        if local:
            for k, v in local.items():
                for diff, count in v.items():
                    try:
                        self.locals[key][func_name][lineno][k][diff] += count   
                    except:
                        if lineno not in self.locals[key][func_name]:
                            self.locals[key][func_name][lineno] = { k : dict() }
                        elif k not in self.locals[key][func_name][lineno]:
                            self.locals[key][func_name][lineno][k] = dict() 

                        self.locals[key][func_name][lineno][k][diff] = count 
                                  
        
    def _check_for_keyword(self, func_name, lineno, line):
        result = dict()
        with open('./keywords.txt', "r") as f:
            for keyword in f.readlines():
                if keyword[:-1] in line:               
                    try:
                        result[keyword[:-1]] += 1
                    except:
                        result[keyword[:-1]] = 1   
        
        if result:
            try:
                self.keywords[func_name][lineno] = result
            except:
                self.keywords[func_name] = { lineno : dict() }
                self.keywords[func_name][lineno] = result

    def _store_returns(self, func_name, lineno, passed, failed):
        try:
            if func_name not in self.returns['passed']:
                self.returns['passed'][func_name] = { lineno : dict() } 

            if passed != '':
                self.returns['passed'][func_name][lineno][passed] += 1
        except:                         
            self.returns['passed'][func_name][lineno][passed] = 1 
            
        try:
            if func_name not in self.returns['failed']:
                self.returns['failed'][func_name] = { lineno : dict() } 

            if failed != '':
                self.returns['failed'][func_name][lineno][failed] += 1
        except:
            self.returns['failed'][func_name][lineno][failed] = 1   

    def _sum_return_lines(self, summary):
        sum = 0
        for k, v in summary.items():
            try:
                val = list(v.values())[0]
                if val > 1:
                    sum += val
            except:
                continue
        try:
            sum /= len(summary.keys())
        except:
            sum = 0

        return sum / 4

    def _locals_to_json(self, locals):
        res = dict()
        try:
            for split in (''.join(locals.split('(')).replace(' ', '')).split(')'):
                token = split.split(':')              
                if len(token) == 2 and "at0x" not in token[1]\
                    and "at 0x" not in token[1]: # Undersök närmre, "cronjob"
                    try:
                        res[token[0]][token[1]] += 1 
                    except:
                        if token[0] not in res.keys():
                            res[token[0]] = dict()

                        res[token[0]][token[1]] = 1 
                        
        except Exception as e:
            print('Converting to json failed, {}'.format(e))
        finally:      
            return res

    def _reset_session(self, func_name)->None:
        self.rnd_probability = 0

        self.divergence = dict()    
        self.keywords   = dict()
        self.locals     = None
        self.returns    = { 'passed' : dict(), 'failed' : dict() }
        self.assertions = { 'passed' : dict(), 'failed' : dict() }

        self.collected_information = {
            'func_name'  : func_name,
            'locals'     : '',
            'assertions' : '',
            'assert_str' : '',
            'returns'    : '',
            'keywords'   : '',
            'divergence' : '',
            'commons'    : ''
        }     

    def summarize_locals(self, func_name): # Fixa till och ta bort all skit som är lambda funktioner..
        """
        Analyzes all locals through all iteartions to locate differing values.
        Note that each line still has data from previous lines and all newly executed lines
        might not alter any locals but maintain thes previous ones. 

        This is not an issue and can be ignored but is presented by only first and last occurence in the
        final report as the lines between are of no interest when the same amount of occurences are present.

        Args:
            func_name - function name
        
        Returns:
            result to be added to rnd_probability, string representation describing differing values on each line.
        """
        arg = ""
        res = 0
        if not self.locals:
            return 0, ""

        for result in self.locals:  
            read = []  
            iterations = self.ts_iterations[result]          
            for lineno, data in self.locals[result][func_name].items():   
                for key, c in data.items():    
                    occurences = len(list(data[key].keys()))            
                    if iterations < 2\
                      or occurences < 2\
                      or key == '_'\
                      or key in read:
                        continue

                    read.append(key)
                    res += occurences / iterations
                    arg += "The local variable \"{}\", gets assigned a different value in {} out of {} {} iterations.\n".format(
                        key, 
                        occurences,
                        iterations, 
                        result)

        return res / 4, arg

    def summarize_returns(self, func_name):
        if not self.returns:
            self.collected_information['returns'] = 'No function calls traced.'
            return

        for result in self.returns:
            for call, vals in self.returns[result].items():
                for lineno, retval in vals.items():
                    try:
                        if len(retval) > 1:
                            self.collected_information['returns'] +=\
                                'Function call to \"{}\" at line {} returns {} different values within {} {} iterations.\n'\
                                .format(
                                    call,
                                    lineno,
                                    len(retval),
                                    len(self.logs[func_name][result].keys()) - 1,
                                    result
                                )
                    except Exception as e:
                        print('Summarize Returns failed, %s' % e)
                        pass
    
    def summarize_keywords(self, func_name):
        if func_name not in self.keywords:
            return

        for lineno, val in self.keywords[func_name].items():
            try:
                keyword = list(val.keys())
                keyword.sort(reverse=True)
            except:
                continue
            
            self.collected_information['keywords'] +=\
                'Keyword \"{}\" located at line {} -> \"{}\".\n'\
                .format(
                    keyword[0],
                    lineno,
                    self.logs[func_name]['passed'][0]['lines'][lineno]['str'].rstrip('\n')
                )

            self.rnd_probability += 0.25

    def summarize_assertions(self, func_name):
        if len(self.assertions['failed']) == 0:
            raise RandReporterException('Needs at least one failed log to work.')

        if len(self.assertions['failed']['str'].keys()) > 1: 
            self.collected_information['assertions'] = 'Assertions fail at more than one location.' 
        
        else:
            # Locate relevant locals used for assertion (if any)
            # Split at "#" to remove any potential comment present in the line. 
            # (Since we only look for variable names we can ignore potential string mishaps)
            try:
                assertion_str = ''.join(
                    list(self.assertions['failed']['str']\
                        .keys())[0]\
                        .split('#')[0])
            except:
                assertion_str = ''
                pass
            
            self.collected_information['assert_str'] = assertion_str
            num_diff = { 'passed' : dict(), 'failed' : dict() }
            try:
                for lineno in self.locals['failed'][func_name]:    
                    for local, vals in self.locals['failed'][func_name][lineno].items():
                        if local in assertion_str:                        
                            num_diff['failed'][local] = len(vals.keys())
                            num_diff['passed'][local] = len(self.locals['passed'][func_name][lineno][local].keys())
            except:
                num_diff[local] = 0
            
            self.rnd_probability += 1   

            if not num_diff['passed']:
                self.collected_information['assertions'] =\
                    'Did not manage to read locals in assertion.\nValues used in assertion differs between {} out of {} passing iterations and {} out of {} failing iterations.\n'.format(
                        len(self.assertions['passed']['trace'].keys()),
                        self.ts_iterations['passed'],
                        len(self.assertions['failed']['trace'].keys()),
                        self.ts_iterations['failed']     
                    )
            else:
                keys = list(num_diff['failed'].keys())
                keys.sort(reverse=True)
                local_a = keys[0]
                try:
                    local_b = keys[1]
                except:
                    local_b = ""

                if local_a == '_': # Fix duplicate..
                    self.collected_information['assertions'] =\
                        '\nDid not manage to read locals in assertion.\nValues used in assertion differs between {} out of {} passing iterations and {} out of {} failing iterations.\n'.format(
                            len(self.assertions['passed']['trace'].keys()),
                            self.ts_iterations['passed'],
                            len(self.assertions['failed']['trace'].keys()),
                            self.ts_iterations['failed'],   
                        )
                    return

                if local_b in local_a:
                    self.collected_information['assertions'] =\
                        'The local variable \"{}\" used in assertion has different values in {} out of {} passed iterations, and {} out of {} failed iterations.\nValues used in assertion differs between {} out of {} passing iterations and {} out of {} failing iterations.'\
                        .format(
                            local_a,
                            num_diff['passed'][local_a],
                            self.ts_iterations['passed'],
                            num_diff['failed'][local_a],
                            self.ts_iterations['failed'],
                            len(self.assertions['passed']['trace'].keys()),
                            self.ts_iterations['passed'],
                            len(self.assertions['failed']['trace'].keys()),
                            self.ts_iterations['failed']
                        )

                    self.rnd_probability += (num_diff['passed'][local_a] + 1) / self.ts_iterations['passed']
                    self.rnd_probability += (num_diff['failed'][local_a] + 1) / self.ts_iterations['failed']
                else:
                    self.collected_information['assertions'] =\
                        'The local variable \"{}\" and local variable \"{}\" used in assertion has different values in {} out of {} iterations and {} out of {} iterations respectively, for passing runs.\nValues used in assertion differs between {} out of {} passing iterations and {} out of {} failing iterations.'\
                        .format(
                            local_a,
                            local_b,
                            num_diff['passed'][local_a],
                            self.ts_iterations['passed'],
                            num_diff['passed'][local_b],
                            self.ts_iterations['passed'],
                            len(self.assertions['passed']['trace'].keys()),
                            self.ts_iterations['passed'],
                            len(self.assertions['failed']['trace'].keys()),
                            self.ts_iterations['failed']
                        )
                    
                    self.rnd_probability += (num_diff['passed'][local_a] + num_diff['failed'][local_a] + 1) / (self.ts_iterations['passed'] + self.ts_iterations['failed'])
                    self.rnd_probability += (num_diff['passed'][local_b] + num_diff['failed'][local_b] + 1) / (self.ts_iterations['passed'] + self.ts_iterations['failed'])        

    def summarize_divergence(self, func_name):
        lineno = list(self.divergence.keys())[0]
        try:
            self.collected_information['commons'] = self.divergence[lineno][func_name]['commons']
            self.collected_information['divergence'] = 'Divergence located at line {}.\nExpected: \"{}\", but got: \"{}\".'.format(
                lineno, 
                self.divergence[lineno][func_name]['expected'], 
                self.divergence[lineno][func_name]['got'])          
        except:
            func = list(self.divergence[lineno].keys())[0]
            self.collected_information['commons'] = self.divergence[lineno][func]['commons']
            self.collected_information['divergence'] = 'Divergence located in called function {}, line {}.\nExpected: \"{}\", but got: \"{}\".'.format(
                func,
                self.divergence[lineno][func]['clineno'], 
                self.divergence[lineno][func]['expected'], 
                self.divergence[lineno][func]['got'])          

    def produce_report(self, func_name, iteration_info):
        if func_name not in self.logs:
            print('Log of traced function {} not found.'.format(func_name))
            raise Exception('Function name not found in ./tracelogs')
        
        self.ts_iterations = iteration_info
        self._reset_session(func_name)
        
        try:        
            self.get_divergence(func_name) 

            local, argument = self.summarize_locals(func_name)
            self.collected_information['locals'] = argument    
            self.rnd_probability += (local * 10)         
            
            self.summarize_returns(func_name)
            self.summarize_keywords(func_name)
            self.summarize_assertions(func_name)               
        except:
            pass
        finally:
            # Compensate for invalid value  
            self.rnd_probability -= 1

        identical_coverage = len(self.divergence.keys()) == 0     
        if not identical_coverage:
            self.summarize_divergence(func_name)
        
        # --- Assertions ---
        if self.ts_iterations['passed'] > 1:
            try:
                tracelen = len(self.assertions['passed']['trace'].keys())
                dif = tracelen / (self.ts_iterations['passed'] - tracelen + 2)        
                if dif == 0 and identical_coverage:
                    self.rnd_probability += 5
                else:
                    self.rnd_probability += 0.5 * dif
            except:
                pass
        
        if self.ts_iterations['failed'] > 1:
            try:
                tracelen = len(self.assertions['failed']['trace'].keys())
                dif = tracelen / (self.ts_iterations['failed'] - tracelen + 2)
                if dif == 1 and identical_coverage:
                    self.rnd_probability += 5
                else:             
                    self.rnd_probability += 0.5 * dif 
            except:
                pass
        
        # --- Returns ---
        if len(self.returns['passed'].keys()) > 1:
            self.rnd_probability += 0.5 * (self._sum_return_lines(self.returns['passed']) - 2) / self.ts_iterations['passed']
        if len(self.returns['failed'].keys()) > 1:
            self.rnd_probability += 0.5 * (self._sum_return_lines(self.returns['failed']) - 2) / self.ts_iterations['failed']

        try:
            final = 1 - 1 / abs(self.rnd_probability)
            if final < 0:
                final = 0
        except:
            final = 0

        try:
            print('Result: {}'.format(final))
            if final < 0.1:
                self._reset_session(func_name) 
            HtmlFormatter.create_html(self.collected_information, final, self.logs['meta'], self.ts_iterations, self.args_reset)  
        except:
            print("HtmlFormatter failed unexpectedly.") 
        
        