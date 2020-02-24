import os
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


def div_daq_controls():
    """
    Generates an HMTL Div containing the DAQ controls
    """
    config_dir = os.environ['DAQ_CFGDIR']
    config_files = [os.path.join(config_dir, f) for f in os.listdir(config_dir)]
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
                value=config_dir+'/config_default.yaml',
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


def div_device_controls():
    """
    Generates an HTML Div containing the DAQ controls
    """
    return html.Div([

        # Title
        html.H4('Device Controls', style={"textAlign": "center"}),

        # Div with the file selection and refresh rate
        html.Div([

            # DAQ device devices setter
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

            html.Div([
                # Buttons that start the DAQ
                dcc.Input(
                    id='input-device-value',
                    placeholder='Enter a value...',
                    type='text',
                    value='',
                    className='one column',
                    disabled=True,
                    style={
                        "display": "flex",
                        "justify-content": "center",
                        "align-items": "center",
                        "width": "55%",
                        'marginTop': '10px',
                        'marginLeft': "10%"
                    }
                ),

                # Buttons that stop the DAQ
                daq.StopButton(
                    id='button-device-set',
                    children='Set',
                    className='one column',
                    disabled=True,
                    style={
                        'marginTop': '10px',
                        "display": "flex",
                        "justify-content": "center",
                        "width": "29%"
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
            "border": "1px solid rgb(216, 216, 216)",
            "position": "relative",
            "height": "400px",
            "marginTop": "10px"
        }
    )


def div_daq_log():
    """
    Generates an HTML Div containing the DAQ log
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
