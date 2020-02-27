import os
import pandas as pd

class VirtualDevice(object):
    def __init__(self, dev_name, meas_keys):
        """
        Virtual file representation of a device. The value of the measurement of
        the device are specified in the file and can be set by writing to the file
        """
        # Check that the DAQ environment has been set
        if 'DAQ_BASEDIR' not in os.environ:
            raise KeyError('DAQ environment not set up, please source setup.sh')

        # Intialize a text file in devices which will contain the measurement values
        self._dev_name  = dev_name
        self._dev_dir   = os.environ['DAQ_DEVDIR']
        self._dev_file  = self._dev_dir+'/'+dev_name

        # Initialize the device measurement keys, names, units and initial values
        self._meas_vals = {key:0. for key in meas_keys}

        # Write the keys and the initial value to a file
        with open(self._dev_file, 'w+') as file:
            val_string = ''
            for i, key in enumerate(self._meas_vals.keys()):
                if i:
                    file.write(',')
                    val_string += ','
                file.write(key)
                val_string += '{:f}'
            file.write('\n')
            val_string += '\n'
            file.write(val_string.format(*self._meas_vals.values()))

    def get_update(self, name):
        """
        Fetches a measurement, updates the last value
        stored and returns the update status
        """
        # Assert the requested key is available
        if name not in self._meas_vals.keys():
            raise KeyError('The VirtualDevice does not contain a value for {}'.format(name))

        # Open the file, get the last entry in the relevant key
        df = pd.read_csv(self._dev_file)
        value = float(df[name].iloc[-1])
        updated = False
        if value != self._meas_vals[name]:
            self._meas_vals[name] = value
            updated = True
        return value, updated

    def get(self, name):
        """
        Fetches a measurement
        """
        # Assert the requested key is available
        if name not in self._meas_vals.keys():
            raise KeyError('The VirtualDevice does not contain a value for {}'.format(name))

        # Open the file, get the last entry in the relevant key
        df = pd.read_csv(self._dev_file)
        return float(df[name].iloc[-1])

    def set(self, name, value):
        """
        Sets the measurement to a new value
        """
        # Assert the requested key is available
        if name not in self._meas_vals.keys():
            raise KeyError('The VirtualDevice does not contain a value for {}'.format(name))

        # Only write if the value is different from the last
        if value != self._meas_vals[name]:
            df = pd.read_csv(self._dev_file)
            df[name].iloc[-1] = value
            df.to_csv(self._dev_file, index=False)
            self._meas_vals[name] = value
