from __future__ import unicode_literals
import sys
import time
import datetime
import json
import argparse
from collections import namedtuple
import numpy as np
import matplotlib.pyplot as plt
import instruments as ik
from utils.logger import Logger, CSVData
from utils.virtual_device import Virtual

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

# Add all the required measurements to the readout chain
Measurement = namedtuple('Measurement', 'inst, meas, scale, name, unit')
measures = []
for key in cfg['measurements'].keys():
    # Determine the instrument to use
    measure = cfg['measurements'][key]
    inst = None
    meas_inst = measure['instrument']
    logger.log("Setting up instrument "+meas_inst)
    if meas_inst == 'dmm6500':
        inst = ik.generic_scpi.SCPIMultimeter
    elif meas_inst == 'fluke3000':
        inst = ik.fluke.Fluke3000
    elif meas_inst == 'virtual':
        inst = Virtual(measure['device'], measure['value'])
    else:
        raise(Exception('Instrument not supported: '+meas_inst))

    # Determine the quantity requested
    meas = None
    meas_quan = measure['quantity']
    logger.log("Setting up "+meas_quan+" measurement")
    if meas_quan == 'current':
        meas = inst.Mode.current_dc
    elif meas_quan == 'voltage':
        meas = inst.Mode.voltage_dc
    elif meas_quan == 'temperature':
        meas = inst.Mode.temperature
    elif meas_quan == 'virtual':
        meas = inst.Mode.default
    else:
        raise(Exception('Quantity not supported: '+meas_quan))

    # Open the requested port
    meas_pro = measure['protocol']
    meas_dev = measure['device']
    logger.log("Initializing device "+meas_dev+" with protocol "+meas_pro)
    if meas_pro == 'usbtmc':
        inst = inst.open_file(meas_dev)
    elif meas_pro == 'serial':
        inst = inst.open_serial(meas_dev, 115200)
    elif meas_pro == 'virtual':
        pass
    else:
        raise(Exception('Protocol not supported: '+meas_pro))
        
    # Append a measurement object
    measures.append(Measurement(
                        inst = inst,
                        meas = meas,
                        scale = measure['scale'],
                        name = measure['name'],
                        unit = measure['unit']))

# Initialize the output file
output = CSVData(OUTPUT_FILE)
logger.log("Creating DAQ output file "+OUTPUT_FILE)

# Create dictionary keys
keys = ['time']
for m in measures:
    keys.append('{} [{}]'.format(m.name, m.unit))
logger.log("DAQ recording keys: ["+",".join(keys)+"]")

# Loop for the requested amount of time 
logger.log("Starting DAQ...")
logger.log("DAQ sampling time: "+(str(SAMPLING_TIME)+' s' if SAMPLING_TIME else 'Unconstrained'))
logger.log("DAQ refresh rate: "+(str(REFRESH_RATE)+' s' if REFRESH_RATE else 'AFAP'))
init_time = time.time()
curr_time = init_time
readings = np.empty(len(measures))
ite_count, perc_count, min_count = 0, 0, 0
while not SAMPLING_TIME or (curr_time - init_time) < SAMPLING_TIME:
    # Read
    for i, m in enumerate(measures):
        readings[i] = m.scale*m.inst.measure(m.meas)
        
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
        message = "DAQ running for {} ({:0.0f}%, {} measurements)".format(elapsed_time, min(ratio, 100), ite_count) 
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
