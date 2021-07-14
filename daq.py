from __future__ import unicode_literals
import os
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
        # Check that the DAQ environment has been set
        if 'DAQ_BASEDIR' not in os.environ:
            raise KeyError('DAQ environment not set up, please source setup.sh')

        # Global parameters
        self._time        = 0.   # Data acquisition time
        self._rate        = 0.   # Minimum time between acquisitions
        self._max_fails   = 16   # Maximum allowed number of failed reads
        self._output_name = ''   # Output file name
        self._output      = None # Output file
        self._max_count   = -1   # Maximum number of entries in a single data file (-1: no limit)
        self._killer      = None # Active instance of the Killer subclass

        # Parse configuration
        self._cfg_name   = ''    # Configuration file name
        self._cfg        = None  # Configuration dictionary
        self.parse_config()

        # Initialize logger
        self._logger     = None  # Logger
        self.initialize_logger()

        # Initialize probes
        self._probes     = []   # Instrument probes
        self._controls   = []   # Instrument controls
        self._data_keys  = []   # List of measurement keys
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
        # Parse command line arguments
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
        cfg_dir = os.environ['DAQ_CFGDIR']
        self._cfg_name = cfg_dir+'/config_default.yaml' if not args.config else args.config
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
        log_dir = os.environ['DAQ_LOGDIR']
        log_name = log_dir+'/{}_{}.log'.format(date_str, self._output_name)
        print("Created new DAQ log under {}".format(log_name))
        self._logger = Logger(log_name)
        self.log("Setting up DAQ with configuration {}".format(self._cfg_name))

    def initialize_probes(self):
        """
        Add all the required probes (lambda functions) to the readout chain.
        """
        inst_types = ['instrument', 'multimeter', 'power_supply', 'virtual']
        Probe = namedtuple('Probe', 'inst, meas, probe, unit, name')
        Control = namedtuple('Control', 'inst, meas, control, vinst, vmeas, vprobe, unit, name')
        self._data_keys = ['time']
        self._probes = []
        self._controls = []
        for k, i in self._cfg['instruments'].items():
            # Set up the instrument
            self.log("Setting up instrument {} of type {}".format(k, i['type']))
            inst = None
            if i['type'] == 'virtual':
                inst = VirtualDevice(k, i['measurements'].keys())
            elif i['type'] in inst_types:
                try:
                    inst = getattr(getattr(ik, i['make']), i['model'])
                except AttributeError:
                    raise ValueError('Instrument {} not found in InstrumentKit'.format(i['model']))
                if 'controls' in i:
                    vinst = VirtualDevice(k, i['controls'])
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
            for k, m in i['measurements'].items():
                self.log("Setting up {} measurement of name {}".format(k, m['name']))
                unit = getattr(pq, m['unit'])
                meas, probe = None, None
                if i['type'] == 'instrument':
                    probe = lambda inst, _: inst.measure()
                elif i['type'] == 'multimeter':
                    meas = getattr(inst.Mode, m['quantity'])
                    probe = lambda inst, meas: inst.measure(meas)
                elif i['type'] == 'virtual':
                    meas = k
                    probe = lambda inst, meas: inst.get(meas)
                    if 'value' in m:
                        inst.set(meas, m['value'])
                elif i['type'] == 'power_supply':
                    if 'channel' in m:
                        inst = inst.channel[m['channel']]
                    inst.output = True
                    meas = inst.__class__.__dict__[m['quantity']]
                    probe = lambda inst, meas: meas.fget(inst)
                    if k in i['controls']:
                        self.log('Setting up controller for {}'.format(m['name']))
                        control = lambda inst, meas, value: meas.fset(inst, value)
                        vprobe = lambda vinst, vmeas: vinst.get_update(vmeas)
                        self._controls.append(Control(inst, meas, control, vinst, k, vprobe, unit, m['name']))
                        if 'value' in m:
                            self.log("Setting {} to {} {}".format(m['name'], m['value'], unit.u_symbol))
                            meas.fset(inst, m['value'])
                            vinst.set(k, m['value'])

                # Append the list of data keys
                self._data_keys.append('{} [{}]'.format(m['name'], unit.u_symbol))

                # Append a probe object
                self._probes.append(Probe(inst, meas, probe, unit, m['name']))

    def initialize_output(self):
        """
        Initialize output file.
        """
        date_str = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())
        data_dir = os.environ['DAQ_DATDIR']
        output_name = data_dir+'/{}_{}.csv'.format(date_str, self._output_name)
        open(output_name, 'w').close()
        self._output = CSVData(output_name)
        self.log("Created DAQ output file {}".format(output_name))
        self.log("DAQ recording keys: [{}]".format(','.join(self._data_keys)))

    def log(self, message, severity=Logger.severity.info):
        """
        Logs a message to the standard output location.
        """
        self._logger.log(message, severity)

    def log_progress(self, delta_t, ite_count, perc_count, min_count):
        """
        Log the DAQ progress
        """
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

        return perc_count, min_count

    def record(self, vals):
        """
        Records the last DAQ readings.
        """
        self._output.record(self._data_keys, vals)
        self._output.write()
        self._output.flush()

    def read(self, probe):
        """
        Reads a specific probe.
        """
        return self._convert_units(probe.probe(probe.inst, probe.meas), probe.unit)

    def handle_fail(self, object, error, fail_count, type):
        """
        Handles a failed read or control of a specific instrument.
        """
        serr, sfat = Logger.severity.error, Logger.severity.fatal
        self.log("Failed to {} {} {} time(s)".format(type, object.name, fail_count), serr)
        self.log("Got instrument error:\n{}".format(error), serr)
        if fail_count == self._max_fails:
            self.log("Too many consecutive fails, killing DAQ...", sfat)
            return False
        elif fail_count and fail_count % 5 == 0:
            self.log("Five consecutive fails, will retry in one minute...", serr)
            for i in range(60):
                if self._killer.kill_now:
                    break
                time.sleep(1)
        else:
            self.log("Will retry in one second...", serr)
            time.sleep(1)

        return True

    def acquire(self):
        """
        Probe the list of requested instruments.
        """
        readings = []
        for p in self._probes:
            for i in range(self._max_fails):
                try:
                    readings.append(float(self.read(p)))
                    break
                except Exception as e:
                    if self._killer.kill_now or not self.handle_fail(p, e, i+1, 'read'):
                        return None

        return readings

    def update_controls(self):
        """
        Check if the virtual power supply controls changed value.
        If they did, update the value of the actual power supply.
        """
        for c in self._controls:
            for i in range(self._max_fails):
                try:
                    value, update = c.vprobe(c.vinst, c.vmeas)
                    break
                except Exception as e:
                    if not self.handle_fail(c, e, i+1, 'read'):
                        return False
            if update:
                for i in range(self._max_fails):
                    try:
                        self.log("Setting {} to {} {}".format(c.name, value, c.unit.u_symbol))
                        c.control(c.inst, c.meas, value)
                        break
                    except Exception as e:
                        if self._killer.kill_now or not self.handle_fail(c, e, i+1, 'set'):
                            return False

        return True

    def run(self):
        """
        Main DAQ function.
        """
        # Give some context
        self.log("Starting DAQ...")
        self.log("DAQ sampling time: "+(str(self._time)+' s' if self._time else 'Unconstrained'))
        self.log("DAQ refresh rate: "+(str(self._rate)+' s' if self._rate else 'AFAP'))

        # Loop for the requested amount of time
        self.initialize_output()
        init_time = curr_time = time.time()
        ite_count, perc_count, min_count = 0, 0, 0
        self._killer = self.Killer()
        while (not self._time or (curr_time - init_time) < self._time) and not self._killer.kill_now:
            # If the current data file contains more than
            # a certain number of lines, create a new one
            if self._max_count > 0 and not ite_count%self._max_count:
                self._output.close()
                self.initialize_output()

            # Acquire measurements, break if None
            readings = self.acquire()
            if not readings:
                break

            # Append the elapsed time
            curr_time = time.time()
            delta_t = curr_time-init_time
            readings = [delta_t]+readings

            # Save readings to disk
            self.record(readings)

            # Update the controlled values
            if not self.update_controls():
                break

            # Wait for next measurement, if minimum time requested
            time.sleep(self._rate)

            # Update, log the progress
            perc_count, min_count = self.log_progress(delta_t, ite_count, perc_count, min_count)

            # Increment iteration count
            ite_count += 1

        # Close the output file
        if self._killer.kill_now:
            self.log("DAQ terminated")
        else:
            self.log("Requested acquisition time completed")
        self.log("Closing DAQ output file")
        self._output.close()

if __name__ == '__main__':
    # Initialize DAQ
    daq = DAQ()

    # Run DAQ
    daq.run()
