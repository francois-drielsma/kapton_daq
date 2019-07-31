from __future__ import unicode_literals
import time
import signal
import datetime
import json
import argparse
import instruments as ik
from collections import namedtuple
from utils.logger import Logger, CSVData
from utils.virtual_device import VirtualDevice

# Class that handles SIGINT and SIGTERM gracefully
class Killer:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)

    def exit(self, signum, frame):
        self.kill_now = True

# Function that acquires the requested measurements
def acquire(probes):
    readings = []
    max_fails = 5
    for i, p in enumerate(probes):
        # Try to get the measurement, allow for a few consecutive failures
        fail_count = 0
        while fail_count < max_fails:
            try:
                readings.append(p.scale*p.probe(p.inst, p.meas))
                break
            except Exception as e:
                logger.log(str(e), logger.severity.error)
                logger.log("Failed to read {}, retrying...".format(p.name), logger.severity.error)
                fail_count += 1
                if fail_count >= max_fails:
                    logger.log("Too many consecutive fails, killing DAQ", logger.severity.fatal)
                    return None

    return readings

# Parse commande line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--config', type=str,
                    help="Sets the config file")
parser.add_argument('--outfile', type=str,
                    help="Sets the output file name")
parser.add_argument('--sampling', type=float,
                    help="Sets the amount of time the DAQ runs for")
parser.add_argument('--refresh', type=float,
                    help="Sets the frequency at which the DAQ takes data")
args = parser.parse_args()

# Load the configuration
cfg_name = 'config/config_default.json'
if args.config:
    cfg_name = args.config

cfg_file = open(cfg_name)
cfg = json.load(cfg_file)

# Global parameters
SAMPLING_TIME = cfg['sampling_time'] if not args.sampling else args.sampling
REFRESH_RATE = cfg['refresh_rate'] if not args.refresh else args.refresh
OUTPUT_FILE = 'data/'+cfg['output_name']+'.csv' if not args.outfile else args.outfile

# Initialize the logger
logger = Logger()
logger.log("Running DAQ with configuration "+cfg_name)

# Initialize the output file
open(OUTPUT_FILE, 'w').close()
output = CSVData(OUTPUT_FILE)
logger.log("Created DAQ output file "+OUTPUT_FILE)

# Add all the required probes (lambda functions) to the readout chain
inst_types = ['instrument', 'multimeter', 'power_supply', 'virtual']
Probe = namedtuple('Probe', 'inst, meas, probe, scale, name, unit')
probes = []
for k, i in cfg['instruments'].items():
    # Set up the instrument
    logger.log("Setting up instrument {} of type {}".format(k, i['type']))
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
        logger.log("Initializing communication protocol {}".format(i['comm']))
        try:
            inst = getattr(inst, 'open_'+i['comm'])(**i['comm_args'])
        except AttributeError:
            raise ValueError('Protocol not supported: {}'.format(i['comm']))

    # Initalize a probe for each measurement
    for m in i['measurements'].values():
        logger.log("Setting up {} measurement of name {}".format(m['quantity'], m['name']))
        meas, probe = None, None
        if i['type'] == 'instrument':
            probe = lambda inst, _: inst.measure()
        elif i['type'] == 'multimeter':
            meas = getattr(inst.Mode, m['quantity'])
            probe = lambda inst, meas: inst.measure(meas)
        else:
            if 'channel' in m:
                inst = inst.channel[m['channel']]
            meas = inst.__class__.__dict__[m['quantity']]
            if 'value' in m:
                logger.log("Setting {} to {} {}".format(m['name'], m['value'], m['unit']))
                meas.fset(inst, m['value'])
                time.sleep(0.1)
            probe = lambda inst, meas: meas.fget(inst)

        # Append a probe object
        probes.append(Probe(inst = inst, meas = meas, probe = probe,
                            scale = m['scale'], name = m['name'], unit = m['unit']))

# Create dictionary keys
keys = ['time']
for m in probes:
    keys.append('{} [{}]'.format(m.name, m.unit))
logger.log("DAQ recording keys: ["+",".join(keys)+"]")

# Loop for the requested amount of time
logger.log("Starting DAQ...")
logger.log("DAQ sampling time: "+(str(SAMPLING_TIME)+' s' if SAMPLING_TIME else 'Unconstrained'))
logger.log("DAQ refresh rate: "+(str(REFRESH_RATE)+' s' if REFRESH_RATE else 'AFAP'))
init_time = time.time()
curr_time = init_time
ite_count, perc_count, min_count = 0, 0, 0
killer = Killer()
while (not SAMPLING_TIME or (curr_time - init_time) < SAMPLING_TIME) and not killer.kill_now:
    # Acquire measurements
    readings = acquire(probes)
    if not readings:
        break

    # Append the output
    vals = [time.time()-init_time]
    vals.extend(readings)
    output.record(keys, vals)
    output.write()
    output.flush()

    # Wait for next measurement, if requested
    time.sleep(REFRESH_RATE)

    # Update, log the progress
    curr_time = time.time()
    delta_t = curr_time-init_time
    ite_count += 1
    if SAMPLING_TIME and int(10*delta_t/SAMPLING_TIME) > perc_count:
        ratio = 100*delta_t/SAMPLING_TIME
        perc_count = int(ratio/10)
        elapsed_time = str(datetime.timedelta(seconds=int(delta_t)))
        message = "DAQ running for {} ({:0.0f}%, {} measurements)".\
                format(elapsed_time, min(ratio, 100), ite_count)
        logger.log(message)
    elif not SAMPLING_TIME and int(delta_t/300) > min_count/5:
        min_count = int(delta_t/60)
        elapsed_time = str(datetime.timedelta(seconds=int(delta_t)))
        message = "DAQ running for {} ({} measurements)".format(elapsed_time, ite_count)
        logger.log(message)

# Close the output file
logger.log("...DONE!")
logger.log("Closing DAQ output file")
output.close()
