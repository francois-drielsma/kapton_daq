import dash
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from plotly import subplots
import plotly.graph_objs as go
import pandas as pd
from os import listdir, killpg, setsid, remove, mkdir
from os.path import join
import errno
import subprocess
import psutil
import signal
import sys
import time
import datetime
import json
import yaml

# Initialize the app
app = dash.Dash(__name__)
server = app.server

# Initialize the directories
dirs = {'dat':'data',
        'cfg':'config',
        'log':'log',
        'dev':'devices'}
for d in dirs.values():
    try:
        mkdir(d)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
        pass

# Function that gets the name and unit from the CSV key
def key_elements(key):
    elmts = key.split(" ")
    name, unit = " ".join(elmts[:-1]), elmts[-1]
    unit = unit.strip("[").strip("]")
    return name, unit

# Function that checks if a process is live
def process_is_live(pid):
    try:
       proc = psutil.Process(int(pid))
       if proc.status() == psutil.STATUS_ZOMBIE:
           return False
       else:
           return True
    except psutil.NoSuchProcess:
        return False

# Function that defines the HTML div that contains the DAQ graph
def div_graph_daq():
    """
    Generates an html Div containing DAQ graph and
    the display options
    """
    return html.Div([
        # Graph division
        html.Div(
            id='div-graph-daq',
            className='nine columns'
        ),
        # List of options for the graph display
        html.Div([
            # Dropdown to choose the file from which to extract the data
            dcc.Dropdown(
                id='dropdown-file-selection',
                options=[],
                clearable=False,
                searchable=False,
                style={'margin-top': '10px'}
            ),

            # Box that shows the elapsed time
            html.Div(
                id="div-time-display",
                style={'margin-top': '10px'}
            ),

            # Choice of graph display type (overlapped or separated)
            html.Div([
                html.H6("Display mode", style={'font-weight': 'bold',
                                               'marginBottom': '0px',
                                               'marginTop': '10px'}),

                dcc.RadioItems(
                    options=[
                        {'label': ' Overlapping', 'value': 'overlap'},
                        {'label': ' Separate (Vertical)', 'value': 'separate_vertical'},
                        {'label': ' Separate (Horizontal)', 'value': 'separate_horizontal'}
                    ],
                    value='overlap',
                    id='radio-display-mode-daq',
                    style={'marginLeft': '5px'}
                )
            ]),

            # Checklist of the measurements to plot and their current values
            html.Div([
                html.Div([
                    html.H6("Display selection", style={'font-weight': 'bold',
                                                        'marginBottom': '0px'}),

                    dcc.Checklist(
                        options = [],
                        value = [],
                        id='checklist-display-options-daq',
                        style={'marginLeft': '5px'}
                    )
                ],
                className='six columns'),

                html.Div(id='div-last-daq-value',
                         className='six columns')
            ],
                className='row',
                style={'margin-top': '10px',
                       'position':'relative'}
            )

        ],
            className='three columns'
        ),
    ],
        className="row",
        style={
            "border-radius": "5px",
            "border-width": "5px",
            "border": "1px solid rgb(216, 216, 216)",
            "position": "relative",
            "height": "480px"
        }
    )

# Function that defines the HTML div that contains the DAQ controls
def div_daq_controls():
    """
    Generates an html Div containing the DAQ controls
    """
    config_files = [join(dirs['cfg'], f) for f in listdir(dirs['cfg'])]
    config_options = [{'label':f.split('/')[-1], 'value':f} for f in config_files]
    return html.Div([

        # Title
        html.H4('DAQ Controls', style={"textAlign": "center"}),

        # Start and stop button
        html.Div([
            # Buttons that start the DAQ
            daq.StopButton(
                id='button-start-daq',
                children='Start',
                className='one column',
                disabled=False,
                style={
                    "display": "flex",
                    "justify-content": "center",
                    "width": "49%",
                }
            ),

            # Buttons that stop the DAQ
            daq.StopButton(
                id='button-stop-daq',
                children='Stop',
                className='one column',
                disabled=True,
                style={
                    "display": "flex",
                    "justify-content": "center",
                    "width": "49%",
                }
            ),
        ]),

        html.Div([
            dcc.Input(
                id='input-output-name',
                type='text',
                value='',
                disabled=False,
                style={
                    "display": "flex",
                    "justify-content": "center",
                    "align-items": "center",
                    "width": "80%",
                    'marginTop': '80px',
                    'marginLeft': "10%"
                }
            ),

            # DAQ config file input block
            dcc.Dropdown(
                id='dropdown-config-selection',
                options=config_options,
                value=dirs['cfg']+'/config_default.yaml',
                className='twelve columns',
                clearable=False,
                searchable=False,
                disabled=False,
                style={
                    "display": "flex",
                    "justify-content": "center",
                    "width": "90%",
                    'marginTop': '5px',
                    'marginLeft': "5%"
                }
            ),

            # Box that display the config file
            dcc.Textarea(
                id="text-config",
                placeholder=" ",
                value="",
                style={
                    "width": "80%",
                    "height": "157px",
                    "marginLeft": "10%",
                    "marginTop": "10px",
                },
                disabled=True
            ),

            # Invisible div that stores the DAQ process ID
            dcc.Store(
                id='store-process-id',
                data=''
            )
        ])
    ],
        className="four columns",
        style={
            "border-radius": "5px",
            "border-width": "5px",
            "border": "1px solid rgb(216, 216, 216)",
            "position": "relative",
            "height": "400px",
            "marginTop": "10px"
        }
    )

# Function that defines the HTML div that contains the device controls
def div_device_controls():
    """
    Generates an html Div containing the DAQ controls
    """
    return html.Div([

        # Title
        html.H4('Device Controls', style={"textAlign": "center"}),

        # Div with the file selection and refresh rate
        html.Div([

            # DAQ device devices setter
            daq.StopButton(
                id='button-device-set',
                children='Set',
                disabled=True,
                style={
                    'marginTop': '10px',
                    "display": "flex",
                    "justify-content": "center",
                    "width": "100%",
                }
            ),

            dcc.Dropdown(
                id='dropdown-device-selection',
                options=[],
                className='twelve columns',
                clearable=False,
                searchable=False,
                disabled=True,
                style={
                    "display": "flex",
                    "justify-content": "center",
                    "width": "90%",
                    'marginTop': '15px',
                    'marginLeft': "5%"
                }
            ),

            dcc.Input(
                id='input-device-value',
                placeholder='Enter a value...',
                type='text',
                value='',
                disabled=True,
                style={
                    "display": "flex",
                    "justify-content": "center",
                    "align-items": "center",
                    "width": "80%",
                    'marginTop': '10px',
                    'marginLeft': "10%"
                }
            )
        ],
            id='div-file-control-0',
            className='row',
            style={'margin-top': 10}
        )
    ],
        className="two columns",
        style={
            "border-radius": "5px",
            "border-width": "5px",
            "border": "1px solid rgb(216, 216, 216)",
            "position": "relative",
            "height": "400px",
            "marginTop": "10px"
        }
    )

# Function that defines the HTML div that contains the DAQ output
def div_daq_log():
    """
    Generates an html Div containing the DAQ controls
    """
    return html.Div([

        # Title
        html.H4('Last DAQ Log', style={"textAlign": "center"}),

        # Start and stop button
        html.Div([
            # Box that display the config file
            dcc.Textarea(
                id="text-log",
                placeholder=" ",
                value="DAQ log will appear here when available...",
                style={
                    "width": "90%",
                    "height": "300px",
                    "marginLeft": "5%",
                    "marginTop": "10px",
                    "background-color":"black",
                    "color":"white"
                },
                disabled=True
            )
        ]),

        # Invisible div that stores the path to the file
        dcc.Store(
            id='store-log-path'
        )
    ],
        #className="six columns",
        style={
            "width": "49%",
            "marginLeft": "50.7%",
            "border-radius": "5px",
            "border-width": "5px",
            "border": "1px solid rgb(216, 216, 216)",
            "position": "relative",
            "height": "400px",
            "marginTop": "10px"
        }
    )

# Define the layout of the full HTML application
app.layout = html.Div([
    # Banner display
    html.Div([
        html.H2(
            'Kapton Data Acquisition',
            id='title'
        ),
        html.Img(
            src="https://www6.slac.stanford.edu/sites/www6.slac.stanford.edu/files/SLAC_Logo_W.png",
            style={
                'height' : '80%',
                'padding-top' : 8
            },
        )
    ],
        className="banner",
        style={
            'width':'96%',
            'margin-top':'2%'
        }
    ),

    # Main HTML division
    html.Div([

        # Element that allows you to update components on a predefined interval
        dcc.Interval(
            id="interval-update",
            n_intervals=0
        ),

        # Invisible div that stores the JSON-serialized dataframe of DAQ data
        dcc.Store(id='store-daq-data'),
        dcc.Store(id='store-daq-keys'),
        dcc.Store(id='store-daq-values'),

        # Html div that stores the DAQ graph and display parameters
        div_graph_daq(),

        # The html div storing the DAQ controls
        div_daq_controls(),

        # The html div storing the device measurement control
        div_device_controls(),

        # The html div storing the DAQ output
        div_daq_log()
    ],
        className="container",
        style={
            'width':'96%'
        }
    )
])

# Function that defines the Dash graph object
def update_graph(daq_data,
                 daq_keys,
                 display_mode,
                 checklist_display_options):
    """
    :param daq_data: the json file containing the data
    :param display_mode: 'separate' or 'overlap'
    :param checklist_display_options: list of keys to display
    :return: dcc Graph object containing the updated figures
    """
    # Check that there is data, return empty graph otherwise
    if not daq_data or not daq_keys:
        return dcc.Graph(id='graph-daq')

    # Import the data, get the keys, check that there is something to display
    daq_df = pd.read_json(daq_data, orient='split')
    keys = []
    for key in daq_keys:
        if key in checklist_display_options:
            keys.append(key)
    n_keys = len(keys)
    if not n_keys:
        return dcc.Graph(id='graph-daq')

    # Use time as the x axis
    times = daq_df['time']

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

    # Initialize the layout
    plotly_layout = go.Layout()

    left_margin = (n_keys-1)*.05
    layout_kwargs = {'title': 'DAQ monitor',
                     'xaxis': {'title': "Time [s]", 'domain':[left_margin, 1]}}

    # Separate the measurements in several vertical graphs
    if display_mode == 'separate_vertical':
        figure = subplots.make_subplots(rows=max(1, n_keys),
                                     cols=1,
                                     print_grid=False,
                                     shared_xaxes=True,
                                     shared_yaxes=False,
                                     vertical_spacing=0.001)

        for i, trace in enumerate(traces):
            figure.append_trace(trace, i+1, 1)

        figure['layout']['title'] = layout_kwargs['title']
        figure['layout']['showlegend'] = False
        figure['layout']['xaxis{}'.format(len(keys))].update(title = 'Time [s]')
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

        figure['layout']['title'] = layout_kwargs['title']
        figure['layout']['showlegend'] = False
        for i, key in enumerate(keys):
            figure['layout']['xaxis'+str(i+1)].update(title = 'Time [s]')
            figure['layout']['yaxis'+str(i+1)].update(title = key)

    # Overlap the measurents on a single canvas
    elif display_mode == 'overlap':
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

# App callback that starts the DAQ when requested to do so,
# records the DAQ process ID to know what to kill,
# disables the start button and enables the stop button,
# initializes the auto-refresh interval
@app.callback([Output('store-process-id', 'data'),
               Output('button-start-daq', 'disabled'),
               Output('button-stop-daq', 'disabled')],
              [Input('button-start-daq', 'n_clicks'),
               Input('button-stop-daq', 'n_clicks')],
              [State('store-process-id', 'data'),
               State('dropdown-config-selection', 'value'),
               State('input-output-name', 'value')])
def daq_controller(nstart, nstop, pid, cfg_name, out_name):
    # If first initialization or stop button pressed, enable the start button
    if nstart is None:
        return '', False, True

    # If no DAQ process is running, start one
    if not pid:
        # Count the amount of files currently in the data directory
        n_files = len(listdir(dirs['dat']))

        # Start the DAQ process
        args = ['python3', 'daq.py', '--config', cfg_name, '--name', out_name]
        pid = subprocess.Popen(' '.join(args), preexec_fn=setsid, shell=True).pid

        # Wait for the program to produce a new data file, as long as it is alive
        while len(listdir(dirs['dat'])) == n_files:
            if not process_is_live(pid):
                return '', False, True
            time.sleep(0.1)

        # Disable the start button
        return str(pid), True, False

    # If there is one running, kill it
    else:
        # Send a kill signal to the DAQ, wait for it to die
        try:
            killpg(int(pid), signal.SIGTERM)
            while process_is_live(pid):
                time.sleep(0.1)
            time.sleep(0.1)
        except:
            print('The DAQ process has already been terminated')
            pass

        # Delete the virtual devices
        dev_files = [join(dirs['dev'], f) for f in listdir(dirs['dev'])]
        for dev in dev_files:
            remove(dev)

        # Disable the stop button, disable autorefresh
        return '', False, True

# App callback that initializes the auto-refresh interval
# when the DAQ is started or stopped (matched to DAQ status)
@app.callback(Output('interval-update', 'interval'),
              [Input('store-process-id', 'data')])
def refresh_interval(pid):
    if pid:
        return 2000             # ms, two seconds
    else:
        return 24*60*60*1000    # ms, one day

# App callback that automatically presses the stop
# button if the DAQ process has died
@app.callback(Output('button-stop-daq', 'n_clicks'),
              [Input('interval-update', 'n_intervals')],
              [State('store-process-id', 'data'),
               State('button-stop-daq', 'n_clicks')])
def check_daq_process(_, pid, nstop):
    if pid and not process_is_live(pid):
        return nstop + 1 if nstop else 1
    else:
        raise PreventUpdate

# App callback that matches the states of the DAQ
# controls to that of the DAQ start button
@app.callback([Output('dropdown-config-selection', 'disabled'),
               Output('input-output-name', 'disabled')],
              [Input('button-start-daq', 'disabled')])
def enable_daq_controls(daq_disable):
    # Match enable status of DAQ controls to start button
    return daq_disable, daq_disable

# App callback that displays the configuration
@app.callback([Output("text-config", "value"),
               Output("input-output-name", "value")],
              [Input('dropdown-config-selection', 'value')])
def update_config_file(cfg_name):
    if cfg_name:
        with open(cfg_name, 'r') as cfg_file:
            cfg = yaml.safe_load(cfg_file)
            return yaml.dump(cfg), cfg['output_name']

    return '', ''

# App callback that matches the states of the device
# controls to that of the DAQ stop button
@app.callback([Output('dropdown-device-selection', 'options'),
               Output('dropdown-device-selection', 'disabled'),
               Output('input-device-value', 'disabled'),
               Output('button-device-set', 'disabled')],
              [Input('button-stop-daq', 'disabled')])
def enable_device_controls(daq_disable):
    # Update the list of device devices
    dev_options = []
    if not daq_disable:
        dev_files = [join(dirs['dev'], f) for f in listdir(dirs['dev'])]
        dev_options = [{'label':f, 'value':f} for f in dev_files]

    # Set the device controls
    return dev_options, daq_disable, daq_disable, daq_disable

# App callback that sets the value of the selected device
# according to the value displayed in the input box
@app.callback(Output('button-device-set', 'label'),
              [Input('button-device-set', 'n_clicks')],
              [State('dropdown-device-selection', 'value'),
               State('input-device-value', 'value')])
def set_device(nclicks, device_name, device_value):
    # If the necessary arguments are not set, skip
    if nclicks is None or not device_name:
        return ''

    # Check that the value provided is a float, write to file
    try:
        float(device_value)
        with open(device_name, 'a+') as device_file:
            device_file.write('\n'+device_value)
    except ValueError:
        pass

    return ''

# App callback that updates the list of available
# data files when the DAQ has created a log file
@app.callback([Output('dropdown-file-selection', 'options'),
               Output('dropdown-file-selection', 'value')],
              [Input('store-process-id', 'data')])
def update_data_list(daq_disable):
    # Update the list of data files, set the last DAQ output as current
    data_files = [join(dirs['dat'], f) for f in listdir(dirs['dat'])]
    data_file = None
    if len(data_files):
        data_files.sort()
        data_file = data_files[-1]
    data_options = [{'label':f.split('/')[-1], 'value':f} for f in data_files]
    return data_options, data_file

# App callback that reads the CSV data file
# when the file selection dropdown is activatived
# or the automatic reload is triggered
@app.callback([Output('store-daq-data', 'data'),
               Output('store-daq-keys', 'data'),
               Output('store-daq-values', 'data')],
              [Input('interval-update', 'n_intervals'),
               Input('dropdown-file-selection', 'value')])
def update_data_file(_, daq_file):
    if daq_file:
        try:
            daq_df = pd.read_csv(daq_file)
            daq_keys = daq_df.keys().to_list()
            daq_values = {key:daq_df[key].iloc[-1] for key in daq_keys}
            if 'time' not in daq_keys:
                print('No time stamps in the data, must provide a \'time\' column')
                return None, [], {}
            daq_keys.remove('time')
            daq_data = daq_df.to_json(orient='split', index=False)
            return daq_data, daq_keys, daq_values
        except FileNotFoundError:
            print('File not found: {}'.format(daq_file))
        except pd.errors.EmptyDataError as error:
            pass

    return None, [], {}

# App callback that updates the list of data keys
# when the file changes, necessary as not all files
# contain the same measurements
@app.callback([Output('checklist-display-options-daq', 'options'),
               Output('checklist-display-options-daq', 'value')],
              [Input('store-daq-keys', 'data')],
              [State('checklist-display-options-daq', 'options'),
               State('checklist-display-options-daq', 'value')])
def update_display_options(daq_keys, disp_options, disp_values):
    if daq_keys:
        options = [{'label': key_elements(key)[0], 'value': key} for key in daq_keys]
        if options == disp_options:
            return disp_options, disp_values

        return options, daq_keys

    return [], []

# App callback that updates the log file displayed
# when the page is refreshed
@app.callback(Output('text-log', 'value'),
              [Input('interval-update', 'n_intervals'),
               Input('store-process-id', 'data')])
def update_log_file(_, __):
    log_files = [join(dirs['log'], f) for f in listdir(dirs['log'])]
    log_file = None
    if len(log_files):
        log_files.sort()
        log_file = log_files[-1]
    if log_file:
        with open(log_file, 'r') as log:
            message = 'Displaying log {}\n\n'.format(log_file)
            return message+''.join(log.readlines())
    else:
        return 'DAQ log will appear here when available...'

# App callback that updates the graph
# whenever the page is refreshed (inherits from store-daq-data)
@app.callback(Output('div-graph-daq', 'children'),
              [Input('radio-display-mode-daq', 'value'),
               Input('checklist-display-options-daq', 'value')],
              [State('store-daq-data', 'data'),
               State('store-daq-keys', 'data')])
def update_div_graph(display_mode,
                     checklist_display_options,
                     daq_data,
                     daq_keys):

    # Update the graph div
    graph = update_graph(daq_data,
                         daq_keys,
                         display_mode,
                         checklist_display_options)

    return [graph]

# App callback that prints the elapsed time
# whenever the page is refreshed (inherits from store-daq-data)
@app.callback(Output('div-time-display', 'children'),
              [Input('store-daq-values', 'data')])
def update_div_time_display(daq_values):
    # If the DAQ is running, get the elapsed time
    time = 0
    if daq_values:
        time = int(daq_values['time'])

    time_delta = str(datetime.timedelta(seconds=time))
    return html.H6(f"Time elapsed: {time_delta}",
                   style={'font-weight': 'bold',
                          'margin-top': '3px'})

# App callback that prints the current values of the measurements
# whenever the page is refreshed (inherits from store-daq-data)
@app.callback(Output('div-last-daq-value', 'children'),
              [Input('store-daq-values', 'data')])
def update_div_last_daq_value(daq_values):
    div = [html.H6("Last values",
                     style={'font-weight': 'bold',
                            'margin-bottom': '0px'}
                    )]
    if daq_values:
        values = []
        for key, value in daq_values.items():
            if key == 'time': continue
            name, unit = key_elements(key)
            val = daq_values[key]
            values.append(html.Div(f"{val:.4f} {unit}",
                style={'marginLeft': '5px', 'font-weight':'bold'}))
        div += values

    return div

# Running the server
if __name__ == '__main__':
    app.run_server(debug=True)
