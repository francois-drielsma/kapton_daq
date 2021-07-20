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

    @app.callback([Output('store-daq-id', 'data'),
                   Output('button-start-daq', 'disabled'),
                   Output('button-stop-daq', 'disabled')],
                  [Input('button-start-daq', 'n_clicks'),
                   Input('button-stop-daq', 'n_clicks')],
                  [State('store-daq-id', 'data'),
                   State('store-controller-id', 'data'),
                   State('dropdown-config-selection', 'value'),
                   State('input-output-name', 'value')])
    def daq_controller(nstart, nstop, daqpid, contpid, cfg_name, out_name):
        '''
        App callback that starts the DAQ when requested to do so,
        records the DAQ process ID to know what to kill,
        disables the start button and enables the stop button
        '''
        # If no DAQ process is running, start one
        if not daqpid:
            # Check that there isn't already a running processes
            pids = find_process('daq.py')
            if len(pids):
                return str(pids[-1]), True, False

            # Count the amount of files currently in the data directory
            n_files = len(os.listdir(os.environ['DAQ_DATDIR']))

            # Start the DAQ process
            args = ['exec', 'python3', os.environ['DAQ_BASEDIR']+'/daq.py', '--config', cfg_name, '--name', out_name]
            daqpid = subprocess.Popen(' '.join(args), shell=True).pid

            # Wait for the program to produce a new data file, as long as it is alive
            while len(os.listdir(os.environ['DAQ_DATDIR'])) == n_files:
                if not process_is_live(daqpid):
                    return '', False, True
                time.sleep(0.1)

            # Disable the start button
            return str(daqpid), True, False

        # If there is one running, kill it
        else:
            # If there is a controller job underway, kill it and wait for it to die
            if contpid:
                try:
                    os.kill(int(contpid), signal.SIGTERM)
                    while process_is_live(pid):
                        time.sleep(0.1)
                    time.sleep(0.1)
                except:
                    pass

            # Send a kill signal to the DAQ, wait for it to die
            try:
                os.kill(int(daqpid), signal.SIGTERM)
                while process_is_live(daqpid):
                    time.sleep(0.1)
                time.sleep(0.1)
            except:
                pass

            # Delete the virtual devices
            dev_dir = os.environ['DAQ_DEVDIR']
            dev_files = [os.path.join(dev_dir, f) for f in os.listdir(dev_dir)]
            for dev in dev_files:
                os.remove(dev)

            # Disable the stop button, disable autorefresh
            return '', False, True


    @app.callback(Output('interval-update', 'disabled'),
                  [Input('store-daq-id', 'data')])
    def refresh_interval(pid):
        '''
        App callback that enables the auto-refresh interval
        when a DAQ process is alive
        '''
        return not bool(pid)


    @app.callback(Output('button-stop-daq', 'n_clicks'),
                  [Input('interval-update', 'n_intervals')],
                  [State('store-daq-id', 'data'),
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
                  [State('store-daq-id', 'data'),
                   State('button-start-daq', 'n_clicks')])
    def update_daq_process(_, pid, nstart):
        '''
        App callback that looks for an already existing
        process running daq.py, raises if multiple are found
        '''
        if not pid:
            pids = find_process('daq.py')
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


    @app.callback([Output('text-config', 'value'),
                   Output('input-output-name', 'value')],
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


    @app.callback([Output('store-controller-id', 'data'),
                   Output('button-set-device', 'disabled'),
                   Output('button-stop-device', 'disabled')],
                  [Input('button-set-device', 'n_clicks'),
                   Input('button-stop-device', 'n_clicks')],
                  [State('store-controller-id', 'data'),
                   State('dropdown-device-selection', 'value'),
                   State('dropdown-meas-selection', 'value'),
                   State('input-device-value', 'value'),
                   State('input-device-step', 'value'),
                   State('input-device-time', 'value')])
    def device_controller(nset, nstop, contpid, device, quantity, value, step, timeint):
        '''
        App callback that starts the Controller when requested to do so,
        records the Controller process ID to know what to kill,
        disables the set button and enables the stop button
        '''
        # If nset is larger than nstop, initialize the controller
        if nstop != nset:
            # Check that there isn't already a running processes
            pids = find_process('controller.py')
            if len(pids):
                return str(pids[-1]), True, False

            # Start the Controller process
            device = device.split('/')[-1]
            args = ['exec', 'python3', os.environ['DAQ_BASEDIR']+'/controller.py', '--device', device,\
                '--quantity', quantity, '--value', str(value), '--step', str(step), '--time', str(timeint)]
            contpid = subprocess.Popen(' '.join(args), shell=True).pid

            # Disable the start button
            return str(contpid), True, False
        else:
            if contpid:
                try:
                    os.kill(int(contpid), signal.SIGTERM)
                    while process_is_live(pid):
                        time.sleep(0.1)
                    time.sleep(0.1)
                except:
                    pass
            daq_pids = find_process('daq.py')
            cont_disable = not bool(len(daq_pids))
            return '', cont_disable, True


    @app.callback(Output('button-stop-device', 'n_clicks'),
                  [Input('interval-update', 'n_intervals'),
                   Input('button-stop-daq', 'disabled')],
                  [State('store-controller-id', 'data'),
                   State('button-stop-device', 'n_clicks'),
                   State('button-set-device', 'disabled'),
                   State('button-stop-device', 'disabled')])
    def check_controller_status(_, daq_disable, pid, nstop, set_disable, stop_disable):
        '''
        App callback that automatically presses the stop
        button if the Controller process has died
        '''
        if pid and not process_is_live(pid):
            return nstop + 1 if nstop else 1
        elif daq_disable and pid and process_is_live(pid):
            return nstop + 1 if nstop else 1
        elif daq_disable or set_disable == stop_disable:
            return nstop
        else:
            raise PreventUpdate


    @app.callback(Output('button-set-device', 'n_clicks'),
                  [Input('button-stop-daq', 'disabled')],
                  [State('store-controller-id', 'data'),
                   State('button-set-device', 'n_clicks'),
                   State('button-stop-device', 'n_clicks')])
    def update_controller_process(_, pid, nset, nstop):
        '''
        App callback that looks for an already existing
        process running controller.py, raises if multiple are found
        '''
        if not pid and nset == nstop:
            pids = find_process('controller.py')
            if len(pids) == 1:
                print('Controller process already running, disabling Set button')
                return nset+1 if nset else 1
            elif len(pids) > 1:
                print('Two or more running Controller processes running, will display the most recent')
                return nset+1 if nset else 1

        raise PreventUpdate


    @app.callback([Output('dropdown-device-selection', 'options'),
                   Output('dropdown-device-selection', 'value'),
                   Output('dropdown-device-selection', 'disabled'),
                   Output('dropdown-meas-selection', 'disabled'),
                   Output('input-device-value', 'disabled'),
                   Output('input-device-step', 'disabled'),
                   Output('input-device-time', 'disabled')],
                  [Input('button-stop-daq', 'disabled')])
    def enable_device_controls(daq_disable):
        '''
        App callback that matches the states of the device
        controls to that of the DAQ stop button
        '''
        # Update the list of device devices
        dev_options = []
        dev_value = None
        if not daq_disable:
            dev_dir = os.environ['DAQ_DEVDIR']
            dev_files = [os.path.join(dev_dir, f) for f in os.listdir(dev_dir)]
            dev_options = [{'label':f.split('/')[-1], 'value':f} for f in dev_files]
            if len(dev_options):
                dev_value = dev_options[0]['value']

        # Set the device controls
        return dev_options, dev_value, daq_disable, daq_disable, daq_disable, daq_disable, daq_disable


    @app.callback([Output('dropdown-meas-selection', 'options'),
                   Output('dropdown-meas-selection', 'value')],
                  [Input('dropdown-device-selection', 'value')])
    def update_device_measurements(device_name):
        '''
        App callback that gets the list of keys from the
        virtual device file
        '''
        # Update the list of device devices
        meas_options = []
        meas_value = None
        if device_name:
            meas_keys = pd.read_csv(device_name).keys()
            meas_options = [{'label':k, 'value':k} for k in meas_keys]
            if len(meas_options):
                meas_value = meas_options[0]['value']

        return meas_options, meas_value


    @app.callback([Output('dropdown-file-selection', 'options'),
                   Output('dropdown-file-selection', 'value')],
                  [Input('store-daq-id', 'data')])
    def update_data_list(_):
        '''
        App callback that updates the list of available
        data files when the DAQ has created a log file
        '''
        # Update the list of data files, set the last DAQ output as current
        data_dir = os.environ['DAQ_DATDIR']
        data_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.csv')]
        data_file = None
        if len(data_files):
            data_files.sort()
            data_file = data_files[-1]
        data_options = [{'label':f.split('/')[-1], 'value':f} for f in data_files]
        return data_options, data_file


    @app.callback([Output('store-daq-keys', 'data')],
                  [Input('interval-update', 'n_intervals'),
                   Input('dropdown-file-selection', 'value')])
    def update_data_keys(_, daq_file):
        '''
        App callback that reads the CSV data file header
        when the file dropdown changes to update the keys
        '''
        if daq_file:
            try:
                # Check that the DAQ file minimally contains a time column
                daq_df = pd.read_csv(daq_file, nrows=1)
                daq_keys = daq_df.keys().to_list()
                if 'time' not in daq_keys:
                    print('No time stamps in the data, must provide a \'time\' column')
                    return []
                daq_keys.remove('time')
                if 'datetime' in daq_keys:
                    daq_keys.remove('datetime')

                return [daq_keys]
            except FileNotFoundError:
                print('File not found: {}'.format(daq_file))
            except pd.errors.EmptyDataError as error:
                pass

        return [[]]


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
                   Input('store-daq-id', 'data')])
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


    @app.callback([Output('div-graph-daq', 'children'),
                   Output('store-daq-values', 'data')],
                  [Input('radio-display-mode-daq', 'value'),
                   Input('checklist-display-options-daq', 'value'),
                   Input('input-time-range', 'value'),
                   Input('dropdown-time-range', 'value')],
                  [State('store-daq-keys', 'data'),
                   State('dropdown-file-selection', 'value')])
    def update_div_graph(display_mode, checklist_display_options, time_value, time_unit, daq_keys, daq_file):
        '''
        App callback that updates the graph
        whenever the page is refreshed
        '''
        # If there are no daq_keys, return blank graph
        if daq_keys is None or not len(daq_keys):
            return (update_graph(None, [], '', '')), {}

        # Read in the datafile
        daq_df = pd.read_csv(daq_file)

        # Restrict the range of time to the requested interval
        time_int = datetime.timedelta(**{time_unit:time_value}).total_seconds()
        daq_df = daq_df[daq_df['time'].iloc[-1]-daq_df['time'] < time_int]
        daq_values = {key:daq_df[key].iloc[-1] for key in daq_df.keys()}

        # If there is no datetime column in the file (older files), add it
        if 'datetime' not in daq_df.keys():
            get_datetimes(daq_file, daq_df)
        else:
            daq_df['datetime'] = pd.to_datetime(daq_df['datetime'], format='%Y-%m-%d_%H-%M-%S.%f')

        # Update the graph
        graph = update_graph(daq_df, daq_keys, display_mode, checklist_display_options)
        return [graph], daq_values


    @app.callback(Output('div-time-display', 'children'),
                  [Input('store-daq-values', 'data')])
    def update_div_time_display(daq_values):
        '''
        App callback that prints the elapsed time
        whenever the page is refreshed
        '''
        # If the DAQ is running, get the elapsed time
        elapsed_time = 0
        if daq_values:
            elapsed_time = int(daq_values['time'])

        time_delta = str(datetime.timedelta(seconds=elapsed_time))
        return html.H6(f"Run time: {time_delta}",
                       style={'font-weight': 'bold',
                              'margin-top': '3px'})


    @app.callback(Output('div-last-daq-value', 'children'),
                  [Input('store-daq-values', 'data')])
    def update_div_last_daq_readings(daq_values):
        '''
        App callback that prints the current values of the measurements
        whenever the page is refreshed
        '''
        div = [html.H6("Last readings",
                         style={'font-weight': 'bold',
                                'margin-bottom': '0px'}
                        )]
        if daq_values:
            values = []
            for key, value in daq_values.items():
                if key == 'time' or key == 'datetime': continue
                name, unit = key_elements(key)
                val = daq_values[key]
                values.append(html.Div(f"{val:.4f} {unit}",
                    style={'margin-left': '5px', 'font-weight':'bold'}))
            div += values

        return div
