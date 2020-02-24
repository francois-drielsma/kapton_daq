import os
import dash

# Check that the environment has been set up
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

# Run the server
if __name__ == '__main__':
    app.run_server(debug=True)
