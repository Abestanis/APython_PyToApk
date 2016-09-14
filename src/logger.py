from exceptions import ValueError
from os.path import isdir
import sys

class Logger(object):
    '''A logging utility implementing five different log levels as well
    as the ability to log to a file, if one is specified.
    '''
    
    PRIORITY_VERBOSE = 0
    PRIORITY_INFO    = 1
    PRIORITY_WARN    = 2
    PRIORITY_ERROR   = 3
    PRIORITY_NONE    = 4
    _priorityPrefix = [
        '',
        '[INFO ] ',
        '[WARN ] ',
        '[ERROR] ',
        '',
    ]
    
    _priority = PRIORITY_INFO
    _logFile  = None
    
    def setLogFile(self, path):
        '''>>> setLogFile(path) -> success
        Setts the output of this logger to the file specified by 'path'.
        This file will be overwritten! Returns True on success.
        '''
        if isdir(path):
            self.warn('Failed to create the log file at ' + path
                      + ': The path points to an existing directory!')
            return False
        self._logFile = open(path, 'w')
        return True
    
    def closeLogFile(self):
        '''>>> closeLogFile()
        Closes the current log file, if one was set.
        '''
        if self._logFile is not None:
            self._logFile.flush()
            self._logFile.close()
            self._logFile = None
    
    def getOutput(self):
        '''>>> getOutput() -> output
        Returns the current output of this logger. Might be a file
        object or stdout.
        '''
        return sys.stdout if self._logFile is None else self._logFile
    
    def setPriority(self, priority):
        '''>>> setPriority(priority)
        Setts the current log level of this logger. Raises
        ValueError if the value is not one of the PRIORITY_* values.
        '''
        if priority < self.PRIORITY_VERBOSE or priority > self.PRIORITY_NONE:
            raise ValueError()
        self._priority = priority
    
    def getLogPriority(self):
        '''>>> getLogPriority() -> priority
        Returns the current log level of this logger.
        '''
        return self._priority
    
    def write(self, msg, isError = False):
        '''>>> write(msg, isError)
        Writes 'msg' to the output of this logger, bypassing
        the priority check. If 'isError' is True and the current
        output of this logger is stdout, stderr will be used instead.
        '''
        if self._logFile == None:
            if isError:
                sys.stderr.write(msg + '\n')
            else:
                print(msg)
        else:
            self._logFile.write(msg + '\n')
    
    def _log(self, priority, msg):
        '''>>> _log(priority, msg)
        Write 'msg' to the current output of this logger,
        if the given 'priority' is higher or equal than the
        current log level. Also, a prefix indicating the
        priority of the message is added.
        '''
        if self._priority <= priority:
            msg = self._priorityPrefix[priority] + str(msg)
            self.write(msg, isError = priority == self.PRIORITY_ERROR)
    
    def verbose(self, msg):
        '''>>> verbose(msg)
        Write the verbose message to the loggers output.
        '''
        self._log(self.PRIORITY_VERBOSE, msg)
    
    def info(self, msg):
        '''>>> info(msg)
        Write the info message to the loggers output.
        '''
        self._log(self.PRIORITY_INFO, msg)
    
    def warn(self, msg):
        '''>>> warn(msg)
        Write the warn message to the loggers output.
        '''
        self._log(self.PRIORITY_WARN, msg)
    
    def error(self, msg):
        '''>>> error(msg)
        Write the error message to the loggers output.
        '''
        self._log(self.PRIORITY_ERROR, msg)
