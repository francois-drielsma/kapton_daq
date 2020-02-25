import os
import sys
import dash
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html

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
                        {'label': ' Overlapping', 'value': 'overlap'},
                        {'label': ' Separate (Vertical)', 'value': 'separate_vertical'},
                        {'label': ' Separate (Horizontal)', 'value': 'separate_horizontal'}
                    ],
                    value='overlap',
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
            dcc.Store(id='store-process-id')
        ])
    ],
        className="four columns",
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
            # DAQ device dropdown selector
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
                    'margin-top': '10px',
                    'margin-left': "5%"
                }
            ),

            # Div with the value input and the setter button
            html.Div([
                # Input box with the value to set the device to
                daq.NumericInput(
                    id='input-device-first',
                    value=0,
                    min=sys.float_info.min,
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
                ),

                # Button that sets the device to the value in the input box
                daq.StopButton(
                    id='button-device-set',
                    children='Set',
                    className='six columns',
                    disabled=True,
                    style={
                        "display": "flex",
                        "justify-content": "center",
                        "width": "50%",
                        "margin-top": "40px"
                    }
                )
            ]),

            html.Div([
                # Input box with the last value to set the device to
                daq.NumericInput(
                    id='input-device-last',
                    value=0,
                    min=sys.float_info.min,
                    max=sys.float_info.max,
                    size=80,
                    label='Last',
                    labelPosition='top',
                    className='four columns',
                    disabled=True,
                    style={
                        "display": "flex",
                        "justify-content": "center",
                        "align-items": "center",
                        "width": "25%",
                        "margin-top": "10px",
                        "margin-left": "10%"
                    }
                ),

                # Input box with the step between each value to set
                daq.NumericInput(
                    id='input-device-step',
                    value=0,
                    min=0,
                    max=sys.float_info.max,
                    size=80,
                    label='Step',
                    labelPosition='top',
                    className='four columns',
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
                        "margin-top": "10px"
                    }
                )
            ])
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
            "margin-right": "0px"
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
            interval=2 * 1000,
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
