from __future__ import unicode_literals
import sys
import time
import json
import argparse
from collections import namedtuple
import numpy as np
import matplotlib.pyplot as plt
import instruments as ik
from utils.logger import CSVData

# Parse commande line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--config', type=str,
                    help="Sets the config file")
parser.add_argument('--name', type=str,
                    help="Sets the output name")
parser.add_argument('--sampling', type=str,
                    help="Sets the amount of time the DAQ runs for")
parser.add_argument('--refresh', type=str,
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
OUTPUT_NAME = cfg['output_name'] if not args.name else args.name

# Add all the required measurements to the readout chain
Measurement = namedtuple('Measurement', 'inst, meas, scale, name, unit')
measures = []
for key in cfg['measurements'].keys():
    # Determine the instrument to use
    measure = cfg['measurements'][key]
    inst, meas = None, None
    meas_type = measure['type']
    if meas_type == 'current':
        inst = ik.generic_scpi.SCPIMultimeter
        meas = inst.Mode.current_dc
    elif meas_type == 'voltage':
        inst = ik.generic_scpi.SCPIMultimeter
        meas = inst.Mode.voltage_dc
    elif meas_type == 'temperature':
        inst = ik.fluke.Fluke3000
        meas = inst.Mode.temperature
    else:
        raise(Exception('Measurement no supported: '+meas_type))

    # Open the requested port
    meas_pro = measure['protocol']
    meas_dev = measure['device']
    if meas_pro == 'usbtmc':
        inst.open_file(meas_dev)
    elif meas_pro == 'serial':
        inst.open_serial(meas_dev, 115200)
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
output_file = "data/{}_{}.csv".format(\
        time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime()), OUTPUT_NAME)
output = CSVData(output_file)

# Create dictionary keys
keys = ['time']
for m in measures:
    keys.append('{} [{}]'.format(m.name, m.unit))

# Loop for the requested amount of time 
init_time = time.time()
readings = np.empty(len(measures))
while not SAMPLING_TIME or (time.time() - init_time) < SAMPLING_TIME:
    # Read
    for i, m in enumerate(measures):
        readings[i] = m.scale*m.inst.measure(m.meas)
        
    if 0. in readings: # TODO failed temp readouts
        continue
    
    # Append the output
    vals = [time.time()-init_time]
    vals.extend(readings)
    output.record(keys, vals)
    output.write()
    output.flush()

    # Wait for next measurement if requested
    time.sleep(REFRESH_RATE)

# Close the output file
output.close()
