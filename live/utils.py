import os
import psutil
import datetime
import numpy as np
import pandas as pd
from plotly import subplots
import plotly.graph_objs as go
from dash import dcc

def key_elements(key):
    '''
    Function that gets the name and unit from the CSV key
    '''
    elmts = key.split(" ")
    name, unit = " ".join(elmts[:-1]), elmts[-1][1:-1]
    return name, unit


def find_process(name):
    '''
    Function that finds existing python processes with name
    '''
    pids = []
    for proc in psutil.process_iter():
        if proc.name() == 'python3':
            proc_dict = proc.as_dict(['pid', 'cmdline'])
            pid = None
            for string in proc_dict['cmdline']:
                if name in string:
                    pid = proc_dict['pid']
                    break
            if pid:
                pids.append(pid)

    return pids


def process_is_live(pid):
    '''
    Function that checks if a process is live
    '''
    try:
       proc = psutil.Process(int(pid))
       if proc.status() == psutil.STATUS_ZOMBIE:
           return False
       else:
           return True
    except psutil.NoSuchProcess:
        return False


def kill_process(pid):
    '''
    Kills a process and wait for it to be dead
    '''
    try:
        os.kill(int(pid), signal.SIGTERM)
        while process_is_live(pid):
            time.sleep(0.1)
        time.sleep(0.1)
    except:
        pass


def get_datetimes(daq_file,
                  daq_df,
                  starttime):
    '''
    Converts the relative time column in a data
    file to a absolute datetime column
    '''
    try:
        sdatetime = pd.to_datetime(os.path.basename(daq_file)[:19], format='%Y-%m-%d_%H-%M-%S')
    except ValueError:
        print('Could not create datetimes, will draw relative time')
        return False
    times = np.array(daq_df['time'])
    datetimes = [sdatetime + datetime.timedelta(seconds=t-starttime) for t in times]
    daq_df['datetime'] = datetimes
    return True


def update_graph(daq_df,
                 daq_keys,
                 display_mode,
                 checklist_display_options):
    """
    Function that defines the Dash graph object

    :param daq_data: the json file containing the data
    :param display_mode: 'separate' or 'overlap'
    :param checklist_display_options: list of keys to display
    :return: dcc Graph object containing the updated figures
    """
    # Check that there is data, return empty graph otherwise
    if daq_df is None or not daq_keys:
        return dcc.Graph(id='graph-daq')

    # Import the data, get the keys, check that there is something to display
    keys = []
    for key in daq_keys:
        if key in checklist_display_options:
            keys.append(key)
    n_keys = len(keys)
    if not n_keys:
        return dcc.Graph(id='graph-daq')

    # Use time as the x axis
    xaxis_title = 'Time [s]'
    times = daq_df['time']
    if 'datetime' in daq_df.keys():
        xaxis_title = ''
        times = daq_df['datetime']

    # Initialize a trace for each quantity measured by the DAQ
    traces = []
    for key in keys:
        values = daq_df[key]
        name, unit = key_elements(key)

        traces.append(go.Scattergl(
            x=times,
            y=values,
            mode='lines',
            name=name
        ))

    # Separate the measurements in several vertical graphs
    if display_mode == 'separate_vertical':
        figure = subplots.make_subplots(rows=max(1, n_keys),
                                        cols=1,
                                        print_grid=False,
                                        shared_xaxes=True,
                                        shared_yaxes=False,
                                        vertical_spacing=0.025)

        for i, trace in enumerate(traces):
            figure.append_trace(trace, i+1, 1)

        figure['layout']['margin'] = {'b':0, 't':30}
        figure['layout']['showlegend'] = False
        figure['layout']['xaxis{}'.format(len(keys))].update(title = xaxis_title)
        for i, key in enumerate(keys):
            figure['layout']['yaxis'+str(i+1)].update(title = key)

    # Separate the measurements in several horizontal graphs
    elif display_mode == 'separate_horizontal':
        figure = subplots.make_subplots(rows=1,
                                        cols=max(1, n_keys),
                                        shared_yaxes=False,
                                        print_grid=False)

        for i, trace in enumerate(traces):
            figure.append_trace(trace, 1, i+1)

        figure['layout']['margin'] = {'b':0, 't':30}
        figure['layout']['showlegend'] = False
        for i, key in enumerate(keys):
            figure['layout']['xaxis'+str(i+1)].update(title = xaxis_title)
            figure['layout']['yaxis'+str(i+1)].update(title = key)

    # Overlap the measurents on a single canvas
    elif display_mode == 'overlap':
        left_margin = (n_keys-1)*.05
        layout_kwargs = {'xaxis':{'title': xaxis_title, 'domain':[left_margin, 1]},
                         'margin': {'b':0, 't':30}}

        for i, key in enumerate(keys):
            axis_name = 'yaxis' + str(i + 1) * (i > 0)
            yaxis = 'y' + str(i + 1) * (i > 0)
            layout_kwargs[axis_name] = {'position': i * 0.05,
                                        'title':key}

            traces[i]['yaxis'] = yaxis
            if i > 0:
                layout_kwargs[axis_name]['overlaying'] = 'y'

        figure = go.Figure(
                    data=traces,
                    layout=go.Layout(layout_kwargs)
                 )

    return dcc.Graph(figure=figure, id='graph-daq')
