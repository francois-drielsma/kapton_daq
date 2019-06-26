from enum import Enum

class Virtual:
    def __init__(self, dev_name, init_val=0.):
        # Intialize a text file in devices which only contains a value
        self.val = init_val
        self.file_name = 'devices/'+dev_name
        with open(self.file_name, 'w+') as virtual_file:
            virtual_file.write(str(init_val))
        
    class Mode(Enum):

        """
        Enum of valid measurement modes for the virtual device
        """
        default = "DEF"
        
    def measure(self, mode=None):
        """
        Reads the virtual device file, output the value read
        """
        value = 0.
        with open(self.file_name, 'r') as virtual_file:
            value = float(virtual_file.readlines()[-1])
        return value

