import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from plotly import tools
import plotly.graph_objs as go
import pandas as pd
from os import listdir
from os.path import join
import datetime

# Take the last data file as an input for the visualizer
data_dir = 'data'
files = [join(data_dir, f) for f in listdir(data_dir)]
files.sort()
DATAFILE = files[-1]

keys = [key for key in list(pd.read_csv(DATAFILE).keys())]
keys.remove('time')

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
    options for smoothing and display, given the list of keys
    """
    mead_div = html.Div(id=f'div-current-daq-value')
    return html.Div([
        # Graph division
        html.Div(
            id=f'div-daq-graph',
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
                    id=f'checklist-display-options-daq'
                )
            ],
                style={'margin-top': '10px'}
            ),

            # Checklist of the measurements to smooth
            html.Div([
                html.P("Smoothing:", style={'font-weight': 'bold', 'margin-bottom': '0px'}),

                dcc.Checklist(
                    options = [{'label': key, 'value': key} for key in keys],
                    values=[],
                    id=f'checklist-smoothing-options-daq'
                )
            ],
                style={'margin-top': '10px'}
            ),

            # Slider that determines the level of smoothing
            html.Div([
                dcc.Slider(
                    min=0,
                    max=1,
                    step=0.2,
                    marks={i / 5: '{}'.format(i / 5) for i in range(0, 6)},
                    value=0.6,
                    updatemode='drag',
                    id=f'slider-smoothing-daq'
                )
            ],
                style={'margin-bottom': '40px'}
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
                    id=f'radio-display-mode-daq'
                ),

                html.Div(id=f'div-current-daq-value')
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
            # Dropdown to choose the file from which to extract the data
            dcc.Dropdown(
                id='dropdown-file-selection',
                options=[{'label':f, 'value':f} for f in files],
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
                className='five columns',
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
            className='row'
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
                 checklist_display_options,
                 checklist_smoothing_options,
                 slider_smoothing):
    """
    :param run_log_json: the json file containing the data
    :param display_mode: 'separate' or 'overlap'
    :param checklist_smoothing_options: list of keys to display
    :param checklist_smoothing_options: list of keys to smooth
    :param slider_smoothing: value between 0 and 1, at interval of 0.05
    :return: dcc Graph object containing the updated figures
    """

    # Smooth the data according to the value specified by the slider
    def smooth(scalars, weight=0.6):
        last = scalars[0]
        smoothed = list()
        for point in scalars:
            smoothed_val = last * weight + (1 - weight) * point
            smoothed.append(smoothed_val)
            last = smoothed_val
        return smoothed
    
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

            # Apply Smoothing if needed
            if key in checklist_smoothing_options:
                values = smooth(values, weight=slider_smoothing)

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

# App callback that updates the refresh rate of the graph 
# when the interval control dropdown is activatived.
# The refresh rate is expressed in [ms]
@app.callback(Output('interval-log-update', 'interval'),
              [Input('dropdown-interval-control', 'value')])
def update_interval_log_update(interval_rate):
    if interval_rate == 'fast':
        return 500

    elif interval_rate == 'regular':
        return 1000

    elif interval_rate == 'slow':
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
    
# App callback that updates the list of keys
# when the file changes
@app.callback([dash.dependencies.Output('checklist-display-options-daq', 'options'),
               dash.dependencies.Output('checklist-display-options-daq', 'values'),
               dash.dependencies.Output('checklist-smoothing-options-daq', 'options'),
               dash.dependencies.Output('checklist-smoothing-options-daq', 'values')],
              [dash.dependencies.Input('run-log-storage', 'children')])
def update_options(_):
    keys = data_keys(DATAFILE)
    options = [{'label': key, 'value': key} for key in keys]
    return options, keys, options, []

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
               Input('checklist-display-options-daq', 'values'),
               Input('checklist-smoothing-options-daq', 'values'),
               Input('slider-smoothing-daq', 'value')])
def update(run_log_json,
           display_mode,
           checklist_display_options,
           checklist_smoothing_options,
           slider_smoothing):

    graph = update_graph(run_log_json,                         
                         display_mode,
                         checklist_display_options,
                         checklist_smoothing_options,
                         slider_smoothing)

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
