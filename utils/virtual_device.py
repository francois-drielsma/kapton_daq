import os

class VirtualDevice:
    def __init__(self, dev_name):
        # Check that the DAQ environment has been set
        if 'DAQ_BASEDIR' not in os.environ:
            raise KeyError('DAQ environment not set up, please source setup.sh')

        # Intialize a text file in devices which only contains a single value
        self._dev_dir = os.environ['DAQ_DEVDIR']
        self._file_name = self._dev_dir+'/'+dev_name

    @property
    def value(self):
        """
        Reads the virtual device file, output the value read
        """
        with open(self._file_name, 'r') as virtual_file:
            return float(virtual_file.readlines()[-1])

    @value.setter
    def value(self, newval):
        with open(self._file_name, 'w+') as virtual_file:
            virtual_file.write(str(newval))
