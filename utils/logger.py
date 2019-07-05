import time
import sys
from enum import Enum

class Logger:

    class severity(Enum):
        """
        Enum with valid severity tags
        """
        debug = "DEBUG"
        info = "INFO"
        warning = "WARNING"
        error = "ERROR"
        fatal = "FATAL"

    def __init__(self, output=''):
        if output:
            self.output = open(output, "a+")
            sys.stdout = self.output
            sys.stderr = sys.stdout

    def log(self, message, severity=severity.info):
        date_str = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())
        message = '['+date_str+']['+severity.value+'] '+message
        print(message, flush=True)

class CSVData:

    def __init__(self, fout):
        self._fout = fout
        self._str  = None
        self._dict = {}

    def record(self, keys, vals):
        for i, key in enumerate(keys):
            self._dict[key] = vals[i]

    def write(self):
        if self._str is None:
            self._fout=open(self._fout,'w')
            self._str=''
            for i,key in enumerate(self._dict.keys()):
                if i:
                    self._fout.write(',')
                    self._str += ','
                self._fout.write(key)
                self._str+='{:f}'
            self._fout.write('\n')
            self._str+='\n'

        self._fout.write(self._str.format(*(self._dict.values())))

    def flush(self):
        if self._fout: self._fout.flush()

    def close(self):
        if self._str is not None:
            self._fout.close()
