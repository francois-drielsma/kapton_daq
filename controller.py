import os
import time
import signal
import argparse
import pandas as pd
import quantities as pq

class Controller:
    """
    Class that handles device controls.
    """
    def __init__(self):
        """
        Initialize shared variables.
        """
        # Check that the DAQ environment has been set
        if 'DAQ_BASEDIR' not in os.environ:
            raise KeyError('DAQ environment not set up, please source setup.sh')

        # Global parameters
        self._device      = '' # Virtual device name
        self._quantity    = '' # Quantity to set
        self._start_value = 0. # First value to set
        self._stop_value  = 0. # Last value to set
        self._step_size   = 0. # Step size between values
        self._step_time   = 30 # Sleep time between each step
        self._max_fails   = 6  # Maximum allowed number of failed set

        # Parse configuration
        self.parse_config()

    # INNER CLASSES #

    class Killer:
        """
        Class that handles SIGINT and SIGTERM gracefully.
        """
        kill_now = False
        def __init__(self):
            signal.signal(signal.SIGINT, self.exit)
            signal.signal(signal.SIGTERM, self.exit)

        def exit(self, signum, frame):
            self.kill_now = True

    # METHODS #

    @staticmethod
    def _convert_units(value, units):
        """
        Check that the value provided has the required units:
        - if it is a `float`, give it the right units;
        - if it is a `Quantity`, rescale to the right units.
        """
        if not isinstance(value, pq.Quantity):
            return pq.Quantity(value, units)
        if units != value.units:
            return value.rescale(units)
        if isinstance(units, pq.unitquantity.UnitTemperature):
            return ik.util_fns.convert_temperature(value, units)
        return value

    def parse_config(self):
        """
        Parse the command line arguments and the configuration file.
        """
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--device', type=str, required=True,
                            help="Sets the device to control")
        parser.add_argument('--quantity', type=str, required=True,
                            help="Sets the device quantity to set")
        parser.add_argument('--value', type=float, required=True,
                            help="Sets the target value to set")
        parser.add_argument('--start', type=float,
                            help="Sets the first value to set")
        parser.add_argument('--step', type=float,
                            help="Sets the step size")
        parser.add_argument('--time', type=float,
                            help="Sets the amount of time between steps")
        args = parser.parse_args()

        # Check that the device exists in the virtual device directory
        dev_dir = os.environ['DAQ_DEVDIR']
        self._device = dev_dir+'/'+args.device
        if not os.path.isfile(self._device):
            raise FileNotFoundError('Could not find the device file under: {}'.format(self._device))

        # Check that the quantity is an entry in the file
        self._quantity = args.quantity
        if self._quantity not in pd.read_csv(self._device).keys():
            raise KeyError('Could not find quantity {} under the device file {}'.\
                                                    format(self._quantity, self._device))

        # Specify the range of values to be set
        self._value = args.value
        if args.step:
            self._start = args.start if args.start is not None else self.read()
            self._step  = args.step
            if self._start > self._value:
                self._step = -abs(self._step)
            self._start += self._step
            self._time  = args.time if args.time else self._time
        else:
            self._start = self._value

    def handle_fail(self, error, fail_count, type):
        """
        Handles a failed read or control.
        """
        serr, sfat = Logger.severity.error, Logger.severity.fatal
        print("Failed to {} {} {} time(s)".format(type, self._device, fail_count), serr)
        print("Got device error:\n{}".format(error), serr)
        if fail_count == self._max_fails:
            print("Too many consecutive fails, killing Controller...", sfat)
            return False
        elif fail_count and fail_count % 5 == 0:
            print("Five consecutive fails, will retry in one minute...", serr)
            time.sleep(60)
        else:
            print("Will retry in one second...", serr)
            time.sleep(1)

        return True

    def read(self):
        """
        Reads the current device quantity value.
        """
        for i in range(self._max_fails):
            try:
                device = pd.read_csv(self._device)
                return float(device[self._quantity].iloc[-1])
            except Exception as e:
                if not self.handle_fail(e, i+1, 'read'):
                    return None

    def set(self, value):
        """
        Sets the current device quantity value.
        """
        for i in range(self._max_fails):
            try:
                device = pd.read_csv(self._device)
                device[self._quantity].iloc[-1] = value
                device.to_csv(self._device, index=False)
                break
            except Exception as e:
                if not self.handle_fail(e, i+1, 'read'):
                    return None

    def control(self):
        """
        Main Controller function.
        """
        value  = self._start
        killer = self.Killer()
        while abs(value-self._start) <= abs(self._value-self._start) and not killer.kill_now:
            # Set the current value
            self.set(value)
            if value == self._value:
                break

            # Increment the value, wait if necessary
            value += self._step
            if abs(value-self._start) <= abs(self._value-self._start):
                time.sleep(self._time)

if __name__ == '__main__':

    # Initialize controller
    control = Controller()

    # Set device
    control.control()
