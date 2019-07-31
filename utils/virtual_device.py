class VirtualDevice:
    def __init__(self, dev_name, init_val=0.):
        # Intialize a text file in devices which only contains a single value
        self.file_name = 'devices/'+dev_name
        self.value = init_val

    @property
    def value(self):
        """
        Reads the virtual device file, output the value read
        """
        value = 0.
        with open(self.file_name, 'r') as virtual_file:
            value = float(virtual_file.readlines()[-1])
        return value

    @value.setter
    def value(self, newval):
        with open(self.file_name, 'w+') as virtual_file:
            virtual_file.write(str(newval))
