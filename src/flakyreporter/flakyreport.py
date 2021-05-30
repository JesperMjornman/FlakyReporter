import sys, platform, os, argparse, json, py, datetime
import flakyreporter.util as util
from shutil import rmtree
from flakyreporter.loghandler import LogHandler
from flakyreporter.randreporter import RandomnessDetector

class FlakyReporter():
    def __init__(self, autorun = True):
        self.args = self._parse_arguments()
        self.num_passed = 0
        self.num_failed = 0               
        self._write_trace_list()

        if autorun:
            if '--scan' in sys.argv:
                if self.args.scan:
                    self.generate_report()
            else:
                args_str = '-vv -s'
                self.run_test_suite(args_str)
                self.generate_report()


    def __del__(self):
        """
        On deconstruction, done to ensure sys.settrace(None) to be executed.
        """
        try:
            sys.settrace(None)
            os.remove('./tracelist.lst')
        except:
            pass

    def run_test_suite(self, args_str) -> None:
        """
        Runs the full test suite or test file, targeting any function
        present in the created trace list.
        """
        self._init_workspace()

        if self.args.file != 'all':
            args_str += ' {}'.format(self.args.file)
        self._run_plugin_trace(args_str)

    def generate_report(self)->None:
        """
        Generates a .html report based on the log files in ./tracelogs
        """
        try:
            logger = LogHandler()
            logger.read_logs(self.args.target)
        except Exception as e:
            print('Failed to read logs, %s' % e)
            return
        
        rdetector = RandomnessDetector(logger.logs, logger.iteration_info, self.args.reset if self.args.reset else False)
        
        for target in self.args.target:
            try:
                rdetector.produce_report(target, logger.iteration_info[target])
            except util.RandReporterException as e:
                print('RandReporter Exception, %s ' % e)
            except Exception as e:
                print('Failed to locate log file \"%s\"' % target)

    def _run_plugin_trace(self, args_str) -> None:
        for _ in range(self.args.iterations):
            try:
                py.test.cmdline.main(args_str.split(" "))
            except:
                pass

    def _init_workspace(self) -> None:
        """
        Creates workspace folders for tracing.
        """
        if self.args.reset:
            try:
                rmtree('./tracelogs')
            except Exception as e:
                print(e)
        try:
            os.mkdir('./tracelogs')
            os.mkdir('./tracelogs/passed')
            os.mkdir('./tracelogs/failed')
        except Exception as e:
            pass    

    def _write_trace_list(self):
        try:
            f = open('tracelist.lst', 'w')
            for func in self.args.target:
                f.write('{}\n'.format(func))
        except Exception as e:
            print(e)

    def _parse_arguments(self):
        """
        Handles parsing of arguments.
        """
        parser = argparse.ArgumentParser(description='Report Random Flakiness')

        parser.add_argument(
            '-s',
            '--scan',
            action='store_true',
            required=False,
            help='scan the target function(s) in the produced tracelogs.'
        )

        parser.add_argument(
            '-t',
            '--target',
            type=str,
            nargs='+',
            required=True,
            help='target function names to trace into'
        )

        parser.add_argument( # Något om kör så här många fails också istället för x antal reruns.
            '-i',
            '--iterations',
            nargs='?',
            const=1,
            required='--scan' not in sys.argv,
            type=int,
            help='number of iterations to run test suite'
        )

        parser.add_argument(
            '-f',
            '--file',
            required='--scan' not in sys.argv,
            help='target test file to trace. If `all` is given, will run all tests.'
        )

        parser.add_argument(
            '-r',
            '--reset',
            required='--scan' not in sys.argv,
            help='define if older log files from earlier session(s) should be erased. Fully resets the workspace.'
        )

        return parser.parse_args()

#if __name__ == '__main__':
#    reporter = FlakyReporter()
    #reporter.dump_meta()
    #args_str = '-vv -s'
    #reporter.run_test_suite(args_str)
    #reporter.fpy_trace._dump_trace_list()
    #py.test.cmdline.main(args_str.split(" "))
    
    # Kör pytest och trams härifrån.