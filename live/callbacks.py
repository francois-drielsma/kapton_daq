import os
import time
import yaml
import signal
import subprocess
import datetime
import numpy as np
import pandas as pd
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from live.utils import *

def register_callbacks(app):

    @app.callback([Output('store-process-id', 'data'),
                   Output('button-start-daq', 'disabled'),
                   Output('button-stop-daq', 'disabled')],
                  [Input('button-start-daq', 'n_clicks'),
                   Input('button-stop-daq', 'n_clicks')],
                  [State('store-process-id', 'data'),
                   State('dropdown-config-selection', 'value'),
                   State('input-output-name', 'value')])
    def daq_controller(nstart, nstop, pid, cfg_name, out_name):
        '''
        App callback that starts the DAQ when requested to do so,
        records the DAQ process ID to know what to kill,
        disables the start button and enables the stop button,
        initializes the auto-refresh interval
        '''
        # If no DAQ process is running, start one
        if not pid:
            # Check that there isn't already a running processes
            pids = find_daq_process()
            if len(pids):
                return str(pids[-1]), True, False

            # Count the amount of files currently in the data directory
            n_files = len(os.listdir(os.environ['DAQ_DATDIR']))

            # Start the DAQ process
            args = ['python3', os.environ['DAQ_BASEDIR']+'/daq.py', '--config', cfg_name, '--name', out_name]
            pid = subprocess.Popen(' '.join(args), preexec_fn=os.setsid, shell=True).pid

            # Wait for the program to produce a new data file, as long as it is alive
            while len(os.listdir(os.environ['DAQ_DATDIR'])) == n_files:
                if not process_is_live(pid):
                    return '', False, True
                time.sleep(0.1)

            # Disable the start button
            return str(pid), True, False

        # If there is one running, kill it
        else:
            # Send a kill signal to the DAQ, wait for it to die
            try:
                os.killpg(int(pid), signal.SIGTERM)
                while process_is_live(pid):
                    time.sleep(0.1)
                time.sleep(0.1)
            except:
                print('The DAQ process has already been terminated')
                pass

            # Delete the virtual devices
            dev_dir = os.environ['DAQ_DEVDIR']
            dev_files = [os.path.join(dev_dir, f) for f in os.listdir(dev_dir)]
            for dev in dev_files:
                os.remove(dev)

            # Disable the stop button, disable autorefresh
            return '', False, True


    @app.callback(Output('interval-update', 'disabled'),
                  [Input('store-process-id', 'data')])
    def refresh_interval(pid):
        '''
        App callback that enables the auto-refresh interval
        when a DAQ process is alive
        '''
        return not bool(pid)


    @app.callback(Output('button-stop-daq', 'n_clicks'),
                  [Input('interval-update', 'n_intervals')],
                  [State('store-process-id', 'data'),
                   State('button-stop-daq', 'n_clicks')])
    def check_daq_status(_, pid, nstop):
        '''
        App callback that automatically presses the stop
        button if the DAQ process has died
        '''
        if pid and not process_is_live(pid):
            return nstop + 1 if nstop else 1
        else:
            raise PreventUpdate


    @app.callback(Output('button-start-daq', 'n_clicks'),
                  [Input('interval-update', 'n_intervals')],
                  [State('store-process-id', 'data'),
                   State('button-start-daq', 'n_clicks')])
    def update_daq_process(_, pid, nstart):
        '''
        App callback that looks for an already existing
        process running daq.py, raises if multiple are found
        '''
        if not pid:
            pids = find_daq_process()
            if len(pids) == 1:
                print('DAQ process already running, disabling Start button')
                return nstart+1 if nstart else 1
            elif len(pids) > 1:
                print('Two or more running DAQ processes running, will display the most recent')
                return nstart+1 if nstart else 1

        raise PreventUpdate


    @app.callback([Output('dropdown-config-selection', 'disabled'),
                   Output('input-output-name', 'disabled')],
                  [Input('button-start-daq', 'disabled')])
    def enable_daq_controls(daq_disable):
        '''
        App callback that matches the states of the DAQ
        controls to that of the DAQ start button
        '''
        # Match enable status of DAQ controls to start button
        return daq_disable, daq_disable


    @app.callback([Output("text-config", "value"),
                   Output("input-output-name", "value")],
                  [Input('dropdown-config-selection', 'value')])
    def update_config_file(cfg_name):
        '''
        App callback that displays the configuration dictionary
        '''
        if cfg_name:
            with open(cfg_name, 'r') as cfg_file:
                cfg = yaml.safe_load(cfg_file)
                return yaml.dump(cfg), cfg['output_name']

        return '', ''


    @app.callback([Output('dropdown-device-selection', 'options'),
                   Output('dropdown-device-selection', 'disabled'),
                   Output('input-device-first', 'disabled'),
                   Output('input-device-last', 'disabled'),
                   Output('input-device-step', 'disabled'),
                   Output('input-device-time', 'disabled'),
                   Output('button-device-set', 'disabled')],
                  [Input('button-stop-daq', 'disabled')])
    def enable_device_controls(daq_disable):
        '''
        App callback that matches the states of the device
        controls to that of the DAQ stop button
        '''
        # Update the list of device devices
        dev_options = []
        if not daq_disable:
            dev_dir = os.environ['DAQ_DEVDIR']
            dev_files = [os.path.join(dev_dir, f) for f in os.listdir(dev_dir)]
            dev_options = [{'label':f.split('/')[-1], 'value':f} for f in dev_files]

        # Set the device controls
        return dev_options, daq_disable, daq_disable, daq_disable, daq_disable, daq_disable, daq_disable


    @app.callback(Output('button-device-set', 'label'),
                  [Input('button-device-set', 'n_clicks')],
                  [State('dropdown-device-selection', 'value'),
                   State('input-device-first', 'value'),
                   State('input-device-last', 'value'),
                   State('input-device-step', 'value'),
                   State('input-device-time', 'value')])
    def set_device(nclicks, device_name, device_first, device_last, device_step, device_time):
        '''
        App callback that sets the value of the selected device
        according to the value displayed in the input boxes
        '''
        # If the necessary arguments are not set, skip
        if nclicks is None or not device_name:
            return ''

        # If the device step is set to 0, set the device to first value
        # Otherwise loop through all the values
        if device_step == 0:
            with open(device_name, 'a+') as device_file:
                device_file.write('\n{:.10f}'.format(device_first))
        else:
            value_scan = np.arange(device_first, device_last, device_step)
            for i, value in enumerate(value_scan):
                with open(device_name, 'a+') as device_file:
                    device_file.write('\n{:.10f}'.format(value))
                if i < len(value_scan)-1:
                    time.sleep(device_time)

        return ''


    @app.callback([Output('dropdown-file-selection', 'options'),
                   Output('dropdown-file-selection', 'value')],
                  [Input('store-process-id', 'data')])
    def update_data_list(_):
        '''
        App callback that updates the list of available
        data files when the DAQ has created a log file
        '''
        # Update the list of data files, set the last DAQ output as current
        data_dir = os.environ['DAQ_DATDIR']
        data_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir)]
        data_file = None
        if len(data_files):
            data_files.sort()
            data_file = data_files[-1]
        data_options = [{'label':f.split('/')[-1], 'value':f} for f in data_files]
        return data_options, data_file


    @app.callback([Output('store-daq-data', 'data'),
                   Output('store-daq-keys', 'data'),
                   Output('store-daq-values', 'data')],
                  [Input('interval-update', 'n_intervals'),
                   Input('dropdown-file-selection', 'value')])
    def update_data_file(_, daq_file):
        '''
        App callback that reads the CSV data file
        when the file selection dropdown is activatived
        or the automatic reload is triggered
        '''
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


    @app.callback([Output('checklist-display-options-daq', 'options'),
                   Output('checklist-display-options-daq', 'value')],
                  [Input('store-daq-keys', 'data')],
                  [State('checklist-display-options-daq', 'options'),
                   State('checklist-display-options-daq', 'value')])
    def update_display_options(daq_keys, disp_options, disp_values):
        '''
        App callback that updates the list of data keys
        when the file changes, necessary as not all files
        contain the same measurements
        '''
        if daq_keys:
            options = [{'label': ' '+key_elements(key)[0], 'value': key} for key in daq_keys]
            if options == disp_options:
                return disp_options, disp_values

            return options, daq_keys

        return [], []


    @app.callback(Output('text-log', 'value'),
                  [Input('interval-update', 'n_intervals'),
                   Input('store-process-id', 'data')])
    def update_log_file(_, __):
        '''
        App callback that updates the log file displayed
        when the page is refreshed
        '''
        log_dir = os.environ['DAQ_LOGDIR']
        log_files = [os.path.join(log_dir, f) for f in os.listdir(log_dir)]
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


    @app.callback(Output('div-graph-daq', 'children'),
                  [Input('radio-display-mode-daq', 'value'),
                   Input('checklist-display-options-daq', 'value')],
                  [State('store-daq-data', 'data'),
                   State('store-daq-keys', 'data')])
    def update_div_graph(display_mode,
                         checklist_display_options,
                         daq_data,
                         daq_keys):
        '''
        App callback that updates the graph
        whenever the page is refreshed (inherits from store-daq-data)
        '''
        # Update the graph div
        graph = update_graph(daq_data,
                             daq_keys,
                             display_mode,
                             checklist_display_options)

        return [graph]


    @app.callback(Output('div-time-display', 'children'),
                  [Input('store-daq-values', 'data')])
    def update_div_time_display(daq_values):
        '''
        App callback that prints the elapsed time
        whenever the page is refreshed (inherits from store-daq-data)
        '''
        # If the DAQ is running, get the elapsed time
        elapsed_time = 0
        if daq_values:
            elapsed_time = int(daq_values['time'])

        time_delta = str(datetime.timedelta(seconds=elapsed_time))
        return html.H6(f"Time elapsed: {time_delta}",
                       style={'font-weight': 'bold',
                              'margin-top': '3px'})


    @app.callback(Output('div-last-daq-value', 'children'),
                  [Input('store-daq-values', 'data')])
    def update_div_last_daq_readings(daq_values):
        '''
        App callback that prints the current values of the measurements
        whenever the page is refreshed (inherits from store-daq-data)
        '''
        div = [html.H6("Last readings",
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
                    style={'margin-left': '5px', 'font-weight':'bold'}))
            div += values

        return div
