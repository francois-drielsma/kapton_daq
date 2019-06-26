import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_daq as daq
from plotly import tools
import plotly.graph_objs as go
import pandas as pd
from os import listdir, killpg, setsid
from os.path import join
import signal
import time
import datetime
import subprocess

# Take the last data file as an input for the visualizer
data_dir = 'data'
data_files = [join(data_dir, f) for f in listdir(data_dir)]
data_files.sort()
DATAFILE = data_files[-1]

keys = [key for key in list(pd.read_csv(DATAFILE).keys())]
keys.remove('time')

# Make a list of the available configurations
config_dir = 'config'
config_files = [join(config_dir, f) for f in listdir(config_dir)]

# Initialize the app
app = dash.Dash(__name__)
server = app.server

# Function that gives you the data keys of a CSV file
def data_keys(data_file):
    keys = [key for key in list(pd.read_csv(DATAFILE).keys())]
    keys.remove('time')
    return keys

# Function that defines the HTML div that conains the graph and its attributes
def div_graph():
    """
    Generates an html Div containing graph and control
    options for display
    """
    mead_div = html.Div(id='div-current-daq-value')
    return html.Div([
        # Graph division
        html.Div(
            id='div-daq-graph',
            className="ten columns"
        ),

        # List of options for the graph display
        html.Div([
            # Checklist of the measurements to plot
            html.Div([
                html.P("Display:", style={'font-weight': 'bold', 'margin-bottom': '0px'}),

                dcc.Checklist(
                    options = [{'label': key, 'value': key} for key in keys],
                    values=keys,
                    id='checklist-display-options-daq'
                )
            ],
                style={'margin-top': '10px'}
            ),

            # Choice of graph display type (overlapped or separated)
            html.Div([
                html.P("Plot Display mode:", style={'font-weight': 'bold', 'margin-bottom': '0px'}),

                dcc.RadioItems(
                    options=[
                        {'label': ' Overlapping', 'value': 'overlap'},
                        {'label': ' Separate (Vertical)', 'value': 'separate_vertical'},
                        {'label': ' Separate (Horizontal)', 'value': 'separate_horizontal'}
                    ],
                    value='overlap',
                    id='radio-display-mode-daq'
                ),

                html.Div(id='div-current-daq-value')
            ]),
        ],
            className="two columns"
        ),
    ],
        className="row"
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
        className="banner"
    ),

    # Main HTML division
    html.Div([
        # Div with the file selection and refresh rate
        html.Div([
            # Buttons that start and stop the DAQ 
            daq.StopButton(
                id='start-button',
                children='Start',
                className='one column',
                disabled=False
            ),
            dcc.Store(
                id='daq-process-id'
            ),

            # DAQ config file input block
            dcc.Dropdown(
                id='dropdown-config-selection',
                options=[{'label':f, 'value':f} for f in config_files],
                value='config/config_default.json',
                className='five columns',
                clearable=False,
                searchable=False,
                disabled=False
            ),

            # DAQ file name input block
            dcc.Input(
                id='input-name',
                placeholder='Enter an output name...',
                type='text',
                value='',
                disabled=False
            )
        ],
            id='div-file-control-0',
            className='row'
        ),

        # Div with the file selection and refresh rate
        html.Div([
            # Buttons that start and stop the DAQ 
            daq.StopButton(
                id='stop-button',
                children='Stop',
                className='one column',
                disabled=True
            ),
        
            # Dropdown to choose the file from which to extract the data
            dcc.Dropdown(
                id='dropdown-file-selection',
                options=[{'label':f, 'value':f} for f in data_files],
                value=DATAFILE,
                className='five columns',
                clearable=False,
                searchable=False
            ),

            # Dropdown to choose the refresh rate of the graph
            dcc.Dropdown(
                id='dropdown-interval-control',
                options=[
                    {'label': 'No Updates', 'value': 'no'},
                    {'label': 'Regular Updates (5s)', 'value': 'regular'},
                    {'label': 'Fast Update (2s)', 'value': 'fast'}
                ],
                value='regular',
                className='four columns',
                clearable=False,
                searchable=False
            ),

            # Box that shows the elapsed time
            html.Div(
                id="div-time-display",
                className="two columns"
            )
        ],
            id='div-file-control',
            className='row',
            style={'marginTop': 10}
        ),

        # Element that allows you to update components on a predefined interval
        dcc.Interval(
            id="interval-log-update",
            n_intervals=0
        ),

        # Hidden Div Storing JSON-serialized dataframe of run log
        html.Div(id='run-log-storage', style={'display': 'none'}),

        # The html div storing the graph and display parameters
        div_graph()
    ],
        className="container"
    )
])

# Function that defines the Dash graph object
def update_graph(run_log_json,
                 display_mode,
                 checklist_display_options):
    """
    :param run_log_json: the json file containing the data
    :param display_mode: 'separate' or 'overlap'
    :param checklist_display_options: list of keys to display
    :return: dcc Graph object containing the updated figures
    """
    
    # Import the data, initialize the graph
    run_log_df = pd.read_json(run_log_json, orient='split')
    keys = []
    for key in data_keys(DATAFILE):
        if key in checklist_display_options:
            keys.append(key)
    n_keys = len(keys)
    if run_log_json and len(keys):

        # Use time as the x axis
        time = run_log_df['time']

        # Initialize a trace for each quantity measured by the DAQ
        traces = []
        for key in keys:
            values = run_log_df[key]

            traces.append(go.Scatter(
                x=time,
                y=values,
                mode='lines',
                name=key
            ))
        
        # Initialize the layout
        plotly_layout = go.Layout()

        left_margin = (n_keys-1)*.05
        layout_kwargs = {'title': 'DAQ monitor',
                         'xaxis': {'title': "Time [s]", 'domain':[left_margin, 1]}}

        # Separate the measurements in several vertical graphs
        if display_mode == 'separate_vertical':
            figure = tools.make_subplots(rows=max(1, n_keys),
                                         cols=1,
                                         print_grid=False,
                                         shared_yaxes=False)

            for i, trace in enumerate(traces):
                figure.append_trace(trace, i+1, 1)

            figure['layout']['title'] = layout_kwargs['title']
            for i, key in enumerate(keys):
                figure['layout']['yaxis'+str(i+1)].update(title = key)

        # Separate the measurements in several horizontal graphs
        elif display_mode == 'separate_horizontal':
            figure = tools.make_subplots(rows=1,
                                         cols=max(1, n_keys),
                                         shared_yaxes=False,
                                         print_grid=False)

            for i, trace in enumerate(traces):
                figure.append_trace(trace, 1, i+1)

            figure['layout']['title'] = layout_kwargs['title']
            for i, key in enumerate(keys):
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

        else:
            figure = None

        return dcc.Graph(figure=figure, id='graph')
        
    return dcc.Graph(id='graph')
    
# App callback that starts the DAQ when requested to do so,
# records the process ID to know what to kill, 
# disables the start button and enables the stop button,
# refreshes the list of files, set the file to last.
# Gets the configuration from the drop down menu,
# gets the file name from the input box.
@app.callback([Output('daq-process-id', 'data'),
               Output('start-button', 'disabled'),
               Output('dropdown-file-selection', 'options'),
               Output('dropdown-file-selection', 'value'),
               Output('dropdown-config-selection', 'disabled'),
               Output('input-name', 'disabled')],
              [Input('start-button', 'n_clicks'),
               Input('stop-button', 'n_clicks')],
              [State('dropdown-config-selection', 'value'),
               State('input-name', 'value')])
def start_daq(nstart, nstop, cfg_name, output_name):
    # If first initialization or stop button pressed, enable the start button
    global data_files
    if nstart is None or nstart == nstop:
        return '', False, [{'label':f, 'value':f} for f in data_files], DATAFILE, False, False

    # Count the amount of files currently in the data directory
    n_files = len(listdir(data_dir))
    
    # Set the arguments to be passed to the daq process
    args = ['python3', 'daq.py', '--config', cfg_name]
    if len(output_name):
        args += ['--name', output_name]
    
    # Initialize the process, record the process ID
    proc = subprocess.Popen(args, preexec_fn=setsid)
    pid = proc.pid
    
    # Wait for the program to produce a new CSV file
    time_out = 60
    init_time = time.time()
    while len(listdir(data_dir)) == n_files and time.time()-init_time < time_out:
        time.sleep(0.2)
    
    # Update the list of data files, set the DAQ update as current
    data_files = [join(data_dir, f) for f in listdir(data_dir)]
    data_files.sort()
    options = [{'label':f, 'value':f} for f in data_files]
    
    # Disable the start button
    return str(pid), True, options, data_files[-1], True, True
    
# App callback that stops the DAQ when requested to do so,
# disables the stop button and enables the start button
@app.callback(Output('stop-button', 'disabled'),
              [Input('start-button', 'n_clicks'),
               Input('stop-button', 'n_clicks')],
              [State('daq-process-id', 'data')])
def stop_daq(nstart, nstop, pid):
    # If the start button was pressed, enable the stop button
    if nstart != nstop:
        return False
        
    # If first initialization, disable the stop button
    if nstop is None:
        return True

    # Send a kill signal to the DAQ
    try:
        killpg(int(pid), signal.SIGTERM)
    except:
        print('The DAQ process has already been terminated')
        pass
    
    # Disable the stop button
    return True

# App callback that updates the refresh rate of the graph 
# when the interval control dropdown is activatived.
# The refresh rate is expressed in [ms]
@app.callback(Output('interval-log-update', 'interval'),
              [Input('dropdown-interval-control', 'value')])
def update_interval_log_update(interval_rate):
    if interval_rate == 'fast':
        return 2 * 1000

    elif interval_rate == 'regular':
        return 5 * 1000

    elif interval_rate == 'no':
        return 24 * 60 * 60 * 1000
        
# App callback that updates the data file to be read 
# when the file selection dropdown is activatived.
# The refresh rate is expressed in [ms]
@app.callback(Output('run-log-storage', 'children'),
              [Input('interval-log-update', 'n_intervals'),
               Input('dropdown-file-selection', 'value')])
def update_data_file(_, file_selection):

    try:
        global DATAFILE
        DATAFILE = file_selection
        run_log_df = pd.read_csv(file_selection)
        json = run_log_df.to_json(orient='split')
    except FileNotFoundError as error:
        print(error)
        print("Please verify if the csv file exists in the data folder.")
        return None

    return json
    
# App callback that updates the list of data keys
# when the file changes, necessary as not all files
# contain the same measurements
@app.callback([Output('checklist-display-options-daq', 'options'),
               Output('checklist-display-options-daq', 'values')],
              [Input('run-log-storage', 'children')])
def update_options(file_selection):
    DATAFILE = file_selection
    keys = data_keys(DATAFILE)
    options = [{'label': key, 'value': key} for key in keys]    
    return options, keys

# App callback that prints the elapsed time
# whenever the page is refreshed (inherits from run-log-storage)
@app.callback(Output('div-time-display', 'children'),
              [Input('run-log-storage', 'children')])
def update_div_time_display(run_log_json):
    if run_log_json:
        run_log_df = pd.read_json(run_log_json, orient='split')
        time = int(run_log_df['time'].iloc[-1]-run_log_df['time'].iloc[0])
        time_delta = str(datetime.timedelta(seconds=time))
        return html.H6(f"Time elapsed: {time_delta}", style={'margin-top': '3px'})

# App callback that updates the graph 
# whenever the page is refreshed (inherits from run-log-storage)
@app.callback(Output('div-daq-graph', 'children'),
              [Input('run-log-storage', 'children'),
               Input('radio-display-mode-daq', 'value'),
               Input('checklist-display-options-daq', 'values')])
def update(run_log_json,
           display_mode,
           checklist_display_options):

    graph = update_graph(run_log_json,                         
                         display_mode,
                         checklist_display_options)

    return [graph]

# App callback that prints the current values of the measurements
# whenever the page is refreshed (inherits from run-log-storage)
@app.callback(Output('div-current-daq-value', 'children'),
              [Input('run-log-storage', 'children')])
def update_div_current_daq_value(run_log_json):
    if run_log_json:
        run_log_df = pd.read_json(run_log_json, orient='split')
        values = []
        for key in data_keys(DATAFILE):
            val = run_log_df[key].iloc[-1]
            values.append(html.Div(f"{key}: {val:.4f}"))
        return [
            html.P(
                "Current values:",
                style={
                    'font-weight': 'bold',
                    'margin-top': '15px',
                    'margin-bottom': '0px'
                },
            ),
            *values
        ]

# Running the server
if __name__ == '__main__':
    app.run_server(debug=True)
