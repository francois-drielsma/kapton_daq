import os
import sys
import dash_daq as daq
from dash import dcc, html

def div_graph_daq():
    """
    Generates an HTML div that contains the DAQ graph
    and the display options
    """
    return html.Div([
        # Graph division
        html.Div(
            id='div-graph-daq',
            className='nine columns',
            style={'margin-left': '10px'}
        ),

        # List of options for the graph display
        html.Div([
            # Dropdown to choose the file from which to extract the data
            dcc.Dropdown(
                id='dropdown-file-selection',
                clearable=False,
                searchable=True,
                style={'margin-top': '10px'}
            ),

            # Selection of the amount of time to represent (not great)
            html.Div([
                html.Div([
                    dcc.Input(
                        id='input-time-range',
                        value=1,
                        type='number',
                        style={"width": "100%"}
                    )],
                    style={'margin-top': '10px'},
                    className='six columns'
                ),
                html.Div([
                    dcc.Dropdown(
                        id='dropdown-time-range',
                        clearable=False,
                        searchable=True,
                        options=[
                            {'label':'second(s)','value':'seconds'},
                            {'label':'minute(s)','value':'minutes'},
                            {'label':'hour(s)','value':'hours'},
                            {'label':'day(s)','value':'days'}],
                        value='hours',
                        style={"width": "100%"}
                    )],
                    style={'margin-top': '10px'},
                    className='six columns'
                )],
                style={'margin-bottom': '10px'},
                className='twelve columns'
            ),

            # Box that shows the elapsed time
            html.Div(
                id="div-time-display",
                style={'margin-top': '10px'}
            ),

            # Choice of graph display type (overlapped or separated)
            html.Div([
                html.H6("Display mode", style={'font-weight': 'bold',
                                               'margin-bottom': '0px',
                                               'margin-top': '10px'}),

                dcc.RadioItems(
                    options=[
                        {'label': ' Separate (Vertical)', 'value': 'separate_vertical'},
                        {'label': ' Separate (Horizontal)', 'value': 'separate_horizontal'},
                        {'label': ' Overlapping', 'value': 'overlap'}
                    ],
                    value='separate_vertical',
                    id='radio-display-mode-daq',
                    style={'margin-left': '5px'}
                )
            ]),

            # Checklist of the measurements to plot and their last readings
            html.Div([
                html.Div([
                    html.H6("Display selection", style={'font-weight': 'bold',
                                                        'margin-bottom': '0px'}),

                    dcc.Checklist(
                        options = [],
                        value = [],
                        id='checklist-display-options-daq',
                        style={'margin-left': '5px'}
                    )
                ],
                className='six columns'),

                html.Div(id='div-last-daq-value',
                         className='six columns')
            ],
                className='row',
                style={'margin-top': '0px',
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
            "border": "2px solid rgb(216, 216, 216)",
            "position": "relative",
            "height": "480px"
        }
    )


def div_daq_controls():
    """
    Generates an HMTL Div containing the DAQ controls
    """
    config_dir = os.environ['DAQ_CFGDIR']
    config_files = [os.path.join(config_dir, f) for f in os.listdir(config_dir)]
    config_options = [{'label':f.split('/')[-1], 'value':f} for f in config_files]
    return html.Div([

        # Title
        html.H4('DAQ Controls', style={"text-align": "center"}),

        # Start and stop button
        html.Div([
            # Button that starts the DAQ
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

            # Button that stops the DAQ
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

        # Div with the config selection
        html.Div([
            # Input box to specify the name of the DAQ file
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
                    'margin-top': '80px',
                    'margin-left': "10%"
                }
            ),

            # DAQ config file dropdown selector
            dcc.Dropdown(
                id='dropdown-config-selection',
                options=config_options,
                value=config_dir+'/config_default.yaml',
                className='twelve columns',
                clearable=False,
                searchable=False,
                disabled=False,
                style={
                    "display": "flex",
                    "justify-content": "center",
                    "width": "90%",
                    'margin-top': '5px',
                    'margin-left': "5%"
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
                    "margin-left": "10%",
                    "margin-top": "10px",
                },
                disabled=True
            ),

            # Invisible div that stores the DAQ process ID
            dcc.Store(id='store-daq-id')
        ])
    ],
        className="three columns",
        style={
            "border-radius": "5px",
            "border-width": "5px",
            "border": "2px solid rgb(216, 216, 216)",
            "position": "relative",
            "height": "400px",
            "margin-top": "10px",
            "margin-left": "0px"
        }
    )


def div_device_controls():
    """
    Generates an HTML Div containing the DAQ controls
    """
    return html.Div([

        # Title
        html.H4('Device Controls', style={"textAlign": "center"}),

        # Div with the device selection
        html.Div([

            # Div with the set and stop buttons
            html.Div([
                # Button that sets the device to the value in the input box
                daq.StopButton(
                    id='button-set-device',
                    children='Set',
                    className='one column',
                    disabled=True,
                    style={
                        "display": "flex",
                        "justify-content": "center",
                        "width": "49%",
                    }
                ),

                # Button that stops the iterative setting of the device
                daq.StopButton(
                    id='button-stop-device',
                    children='Stop',
                    className='one column',
                    disabled=True,
                    style={
                        "display": "flex",
                        "justify-content": "center",
                        "width": "49%",
                    }
                )
            ]),

            # DAQ device dropdown selector
            dcc.Dropdown(
                id='dropdown-device-selection',
                options=[],
                className='twelve columns',
                clearable=False,
                searchable=False,
                disabled=True,
                placeholder='Select the device to control',
                style={
                    "display": "flex",
                    "justify-content": "center",
                    "width": "90%",
                    'margin-top': '25px',
                    'margin-left': "5%"
                }
            ),

            # DAQ device dropdown selector
            dcc.Dropdown(
                id='dropdown-meas-selection',
                options=[],
                className='twelve columns',
                clearable=False,
                searchable=False,
                disabled=True,
                placeholder='Select the quantity to set',
                style={
                    "display": "flex",
                    "justify-content": "center",
                    "width": "90%",
                    'margin-top': '5px',
                    'margin-left': "5%"
                }
            ),

            # Div with the value input and the start value
            html.Div([
                # Input box with the value to set the device to
                daq.NumericInput(
                    id='input-device-value',
                    value=0,
                    min=-sys.float_info.max,
                    max=sys.float_info.max,
                    size=80,
                    label='Value',
                    labelPosition='top',
                    className='six columns',
                    disabled=True,
                    style={
                        "display": "flex",
                        "justify-content": "center",
                        "align-items": "center",
                        "width": "25%",
                        "margin-top": "10px",
                        "margin-left": "10%"
                    }
                )
            ]),

            # Div with the step size and the time delay between steps
            html.Div([
                # Input box with the step between each value to set
                daq.NumericInput(
                    id='input-device-step',
                    value=0,
                    min=0,
                    max=sys.float_info.max,
                    size=80,
                    label='Step',
                    labelPosition='top',
                    className='six columns',
                    disabled=True,
                    style={
                        "display": "flex",
                        "justify-content": "center",
                        "align-items": "center",
                        "width": "25%",
                        "margin-top": "10px"
                    }
                ),

                # Input box with the time to wait between each value to set
                daq.NumericInput(
                    id='input-device-time',
                    value=30,
                    min=1,
                    max=3600,
                    size=80,
                    label='Time',
                    labelPosition='top',
                    className='four columns',
                    disabled=True,
                    style={
                        "display": "flex",
                        "justify-content": "center",
                        "align-items": "center",
                        "width": "25%",
                        "margin-top": "10px",
                        "margin-bottom": "40px"
                    }
                )

            ]),

            # Invisible div that stores the device controller process ID
            dcc.Store(id='store-controller-id')
        ],
            id='div-file-control-0',
            className='row',
            style={'margin-top': 10}
        )
    ],
        className="three columns",
        style={
            "border-radius": "5px",
            "border-width": "5px",
            "border": "2px solid rgb(216, 216, 216)",
            "position": "relative",
            "height": "400px",
            "margin-top": "10px"
        }
    )


def div_daq_log():
    """
    Generates an HTML Div containing the DAQ log
    """
    return html.Div([

        # Title
        html.H4('Last DAQ Log', style={"textAlign": "center"}),

        # Div to display the DAQ output log
        html.Div([
            # Box that display the DAQ log
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

        # Invisible div that stores the path to the log file
        dcc.Store(
            id='store-log-path'
        )
    ],
        className="six columns",
        style={
            "border-radius": "5px",
            "border-width": "5px",
            "border": "2px solid rgb(216, 216, 216)",
            "position": "relative",
            "height": "400px",
            "margin-top": "10px",
            "margin-right": "0px",
            "width": "55%"
        }
    )

# Main page layout
layout = html.Div([
    # Banner display
    html.Div([
        html.H2(
            'Kapton Data Acquisition',
            id='title'
        ),
        html.Img(
            src="https://www6.slac.stanford.edu/sites/www6.slac.stanford.edu/files/SLAC_Logo_W.png",
            style={
                'height': '80%',
                'padding-top': 8
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
            interval=2 * 1000,
            n_intervals=0
        ),

        # Invisible div that stores the JSON-serialized dataframe of DAQ data
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
