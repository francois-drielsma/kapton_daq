class VirtualDevice:
    def __init__(self, dev_name):
        # Intialize a text file in devices which only contains a single value
        self._file_name = 'devices/'+dev_name

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
