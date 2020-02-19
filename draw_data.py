import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys

# Get the data file
if 'csv' not in sys.argv[-1]:
    raise Exception('Please specify a csv file in the command line')

# Import the data content with pandas
name = sys.argv[-1].split('/')[-1].split('.')[0]
data = pd.read_csv(sys.argv[-1])

# Initialize the relative time array
init_time = np.full(data.shape[0], data['time'][0])
time = data['time'] - init_time

# Draw all quantities as a function of time
for key in data.keys():
    if 'time' in key:
        
        continue
    plt.plot(time, data[key])
    plt.xlabel('Time [s]')
    plt.ylabel(key)
    plt.savefig('output/'+name+'_'+key.split(' [')[0].lower()+'.pdf')
