import os
import dash
import argparse

# Check that the DAQ environment has been set
if 'DAQ_BASEDIR' not in os.environ:
    raise KeyError('DAQ environment not set up, please source setup.sh')

# Initialize the app
app = dash.Dash(__name__)
server = app.server

# Import the layout of the application
from live.layout import layout
app.layout = layout

# Register the callbacks
from live.callbacks import register_callbacks
register_callbacks(app)

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=8050,
                    help="Sets the Flask server port number (default: 8050)")
parser.add_argument('--host', type=str, default='127.0.0.1',
                    help="Sets the Flask server host address (default: 127.0.0.1)")
args = parser.parse_args()

# Run the server
if __name__ == '__main__':
    app.run_server(debug=True, port=args.port, host=args.host)
