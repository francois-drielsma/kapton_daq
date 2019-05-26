from __future__ import unicode_literals

import instruments as ik
import time
import matplotlib.pyplot as plt
import numpy as np
from collections import namedtuple
from utils.logger import CSVData

# Structure that contains the measurements to be recorded at each cycle
Measurement = namedtuple("Measurement", "inst, meas, scale, name, unit")

# Global parameters
SAMPLING_TIME = 0     # In seconds. If 0, record continuously until a KB interrupt
REFRESH_RATE = 0      # In seconds. If 0, go as fast as the instruments can cope 
OUTPUT_FILE_NAME = 'kapton_daq'

# Add all the required measurements to the readout chain
meas = []

inst = ik.generic_scpi.SCPIMultimeter.open_file('/dev/usbtmc0')
dci = Measurement(
        inst = inst,
        meas = insts[0].Mode.current_dc,
        scale = 1.e9,
        name = 'Current',
        unit = 'nA')
meas.append(dci)

inst = ik.fluke.Fluke3000.open_serial('/dev/ttyUSB0', 115200)
temp = Measurement(
        inst = inst,
        meas = inst.Mode.temperature,
        scale = 1.,
        name = 'Temperature',
        unit = 'C')
meas.append(temp)

# Initialize the output file
output_file = "data/{}_{}.csv".format(int(time.time()), OUTPUT_FILE_NAME)
output = CSVData(output_file)

# Create dictionary keys
keys = []
for m in meas:
    keys.append('{} [{}]'.format(m.name, m.unit))

# Loop for the requested amount of time 
init_time = time.time()
readings = np.empty(len(meas))
while not SAMPLING_TIME or (time.time() - init_time) < SAMPLING_TIME:
    # Read
    for i, m in enumerate(meas):
        readings[i] = m.scale*m.inst.measure(m.meas)
    
    # Append the output
    vals = [time.time()]
    vals.extend(readings)
    output.record(keys, vals)
    output.write()

    # Wait for next measurement if requested
    time.sleep(REFRESH_RATE)

# Close the output file
output.close()
