from __future__ import unicode_literals
import time
import signal
import datetime
import yaml
import argparse
import instruments as ik
import quantities as pq
from collections import namedtuple
from utils.logger import Logger, CSVData
from utils.virtual_device import VirtualDevice

class DAQ:
    """
    Class that handles data acquisition.
    """
    def __init__(self):
        """
        Initialize shared variables.
        """
        # Global parameters
        self._time = 0.         # Data acquisition time
        self._rate = 0.         # Minimum time between acquisitions
        self._max_fails = 16    # Maximum allowed number of failed reads
        self._output_name = ''  # Output file name
        self._output = None     # Output file

        # Parse configuration
        self._cfg_name = ''     # Configuration file name
        self._cfg = None        # Configuration dictionary
        self.parse_config()

        # Initialize logger
        self._logger = None     # Logger
        self.initialize_logger()

        # Initialize probes
        self._probes = []       # Instrument probes
        self._data_keys = []    # List of measurement keys
        self.initialize_probes()

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
        # Parse commande line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--config', type=str,
                            help="Sets the config file")
        parser.add_argument('--name', type=str,
                            help="Sets the DAQ name")
        parser.add_argument('--sampling', type=float,
                            help="Sets the amount of time the DAQ runs for")
        parser.add_argument('--refresh', type=float,
                            help="Sets the frequency at which the DAQ takes data")
        args = parser.parse_args()

        # Load the configuration
        self._cfg_name = 'config/config_default.yaml' if not args.config else args.config
        with open(self._cfg_name, 'r') as cfg_file:
            self._cfg = yaml.safe_load(cfg_file)

        # Set global parameters
        self._time = self._cfg['sampling_time'] if not args.sampling else args.sampling
        self._rate = self._cfg['refresh_rate'] if not args.refresh else args.refresh
        self._output_name = self._cfg['output_name'] if not args.name else args.name

    def initialize_logger(self):
        """
        Initialize a Logger object.
        """
        date_str = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())
        log_name = 'log/{}_{}.log'.format(date_str, self._output_name)
        print("Created new DAQ log under {}".format(log_name))
        self._logger = Logger(log_name)
        self.log("Setting up DAQ with configuration {}".format(self._cfg_name))

    def initialize_probes(self):
        """
        Add all the required probes (lambda functions) to the readout chain.
        """
        inst_types = ['instrument', 'multimeter', 'power_supply', 'virtual']
        Probe = namedtuple('Probe', 'inst, meas, probe, unit, name')
        self._data_keys = ['time']
        self._probes = []
        for k, i in self._cfg['instruments'].items():
            # Set up the instrument
            self.log("Setting up instrument {} of type {}".format(k, i['type']))
            inst = None
            if i['type'] == 'virtual':
                inst = VirtualDevice(k)
            elif i['type'] in inst_types:
                try:
                    inst = getattr(getattr(ik, i['make']), i['model'])
                except AttributeError:
                    raise ValueError('Instrument {} not found in InstrumentKit'.format(i['model']))
            else:
                raise ValueError('Instrument type not supported: {}'.format(i['type']))

            # Initialize the communication link
            if i['type'] != 'virtual':
                self.log("Initializing communication protocol {}".format(i['comm']['type']))
                try:
                    inst = getattr(inst, 'open_'+i['comm']['type'])(**i['comm']['args'])
                except AttributeError:
                    raise ValueError('Protocol not supported: {}'.format(i['comm']['type']))

            # Initalize a probe for each measurement
            for m in i['measurements'].values():
                self.log("Setting up {} measurement of name {}".format(m['quantity'], m['name']))
                unit = getattr(pq, m['unit'])
                meas, probe = None, None
                if i['type'] == 'instrument':
                    probe = lambda inst, _: inst.measure()
                elif i['type'] == 'multimeter':
                    meas = getattr(inst.Mode, m['quantity'])
                    probe = lambda inst, meas: inst.measure(meas)
                else:
                    if i['type'] == 'power_supply':
                        if 'channel' in m:
                            inst = inst.channel[m['channel']]
                        time.sleep(1)
                        inst.output = True

                    meas = inst.__class__.__dict__[m['quantity']]
                    if 'value' in m:
                        self.log("Setting {} to {} {}".format(m['name'], m['value'],unit.u_symbol))
                        meas.fset(inst, m['value'])
                        time.sleep(0.1)

                    probe = lambda inst, meas: meas.fget(inst)

                # Append the list of data keys
                self._data_keys.append('{} [{}]'.format(m['name'], unit.u_symbol))

                # Append a probe object
                self._probes.append(Probe(inst, meas, probe, unit, m['name']))


    def initialize_output(self):
        """
        Initialize output file.
        """
        date_str = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())
        output_name = 'data/{}_{}.csv'.format(date_str, self._output_name)
        open(output_name, 'w').close()
        self._output = CSVData(output_name)
        self.log("Created DAQ output file {}".format(output_name))
        self.log("DAQ recording keys: [{}]".format(','.join(self._data_keys)))

    def log(self, message, severity=Logger.severity.info):
        """
        Logs a message to the standard output location.
        """
        self._logger.log(message, severity)

    def read(self, probe):
        """
        Reads a specific probe.
        """
        return self._convert_units(probe.probe(probe.inst, probe.meas), probe.unit)

    def handle_fail(self, probe, error, fail_count):
        """
        Handles a failed read from a specific probe.
        """
        serr, sfat = Logger.severity.error, Logger.severity.fatal
        self.log("Failed to read {} {} time(s)".format(probe.name, fail_count), serr)
        self.log("Got instrument reading error:\n{}".format(error), serr)
        if fail_count == self._max_fails:
            self.log("Too many consecutive fails, killing DAQ...", sfat)
            return False
        elif fail_count and fail_count % 5 == 0:
            self.log("Five consecutive fails, will retry in one minute...", serr)
            time.sleep(60)
        else:
            self.log("Will retry in one second...", serr)
            time.sleep(1)

        return True

    def acquire(self):
        """
        Probe the list of requested instruments.
        """
        readings = []
        for i, p in enumerate(self._probes):
            for i in range(self._max_fails):
                try:
                    readings.append(float(self.read(p)))
                    break
                except Exception as e:
                    if not self.handle_fail(p, e, i+1):
                        return None

        return readings

    def run(self):
        """
        Main DAQ function.
        """
        # Initialize the output file
        self.initialize_output()

        # Give some context
        self.log("Starting DAQ...")
        self.log("DAQ sampling time: "+(str(self._time)+' s' if self._time else 'Unconstrained'))
        self.log("DAQ refresh rate: "+(str(self._rate)+' s' if self._rate else 'AFAP'))

        # Loop for the requested amount of time
        init_time = curr_time = time.time()
        ite_count, perc_count, min_count = 0, 0, 0
        killer = self.Killer()
        while (not self._time or (curr_time - init_time) < self._time) and not killer.kill_now:
            # Acquire measurements, break if None
            readings = self.acquire()
            if not readings:
                break

            # Append the elapsed time
            curr_time = time.time()
            delta_t = curr_time-init_time
            readings = [delta_t]+readings

            # Save to disk
            self._output.record(self._data_keys, readings)
            self._output.write()
            self._output.flush()

            # Wait for next measurement, if minimum time requested
            time.sleep(self._rate)

            # Update, log the progress
            ite_count += 1
            if self._time and int(10*delta_t/self._time) > perc_count:
                ratio = 100*delta_t/self._time
                perc_count = int(ratio/10)
                elapsed_time = str(datetime.timedelta(seconds=int(delta_t)))
                message = "DAQ running for {} ({:0.0f}%, {} measurements)".\
                        format(elapsed_time, min(ratio, 100), ite_count)
                self.log(message)
            elif not self._time and int(delta_t/300) > min_count/5:
                min_count = int(delta_t/60)
                elapsed_time = str(datetime.timedelta(seconds=int(delta_t)))
                message = "DAQ running for {} ({} measurements)".format(elapsed_time, ite_count)
                self.log(message)

        # Close the output file
        self.log("...DONE!")
        self.log("Closing DAQ output file")
        self._output.close()

if __name__ == '__main__':
    # Initialize DAQ
    daq = DAQ()

    # Run DAQ
    daq.run()
