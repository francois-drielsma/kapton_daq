## Package description

Package that centralizes all the resources necessary
to setup the data acquisition for the Kapton sheet
resistance measurement at cryogenic temperatures

## Prerequisites

This package is written in Python 3.

The following packages must be installed:

```bash
pip3 install plotly dash dash_daq psutil pandas numpy matplotlib
```

## Install the InstrumentKit (`IK`) repository

The InstrumentKit package supports communications through
a variety of protocols (GPIB, RS232, USBTMC, etc.). Only
the fork of `francois-drielsma` supports the Fluke 3000 FC,
Keithley 485, HP E3631A and Glassman FR-series devices,
so pull that one specifically.

1. Pull the repository

```bash
git clone https://github.com/francois-drielsma/InstrumentKit
```

2. Install the package

```bash
cd InstrumentKit/
sudo python3 setup.py install
```

### Enable serial connections

1. Add yourself as user of the tty and dialout groups

```bash
sudo adduser user tty
sudo adduser user dialout
```

2. Reboot the computer

### Enable USBTMC devices

1. Connect the device and identify its vendor and model ID:

```bash
lsusb
Bus 001 Device 016: ID 05e6:6500 Keithley Instruments
```

2. Add udev rules to handle the device

```bash
sudo vim /etc/udev/rules.d/usbtmc.rules
```
then write
```
# USBTMC instruments

# Keithley DMM6500
SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="05e6", ATTRS{idProduct}=="6500", GROUP="usbtmc", MODE="0660"

# Devices
KERNEL=="usbtmc/*",       MODE="0660", GROUP="usbtmc"
KERNEL=="usbtmc[0-9]*",   MODE="0660", GROUP="usbtmc"
```

3. Add the corresponding group, add yourself as user

```bash
sudo addgroup usbtmc
sudo adduser user usbtmc
```

4. Reboot the computer

## Use the live DAQ

Simply run

```bash
python3 daq_live.py
```
and then open the app into a browser (click on the link in the terminal).

The DAQ live viewer currently contains the following features:
  - Live graph(s) of the measurements performed by the DAQ
    - Display of elapsed DAQ time
    - Data file selector
    - Selection of curves to display
    - Selection of display style
    - Display of last readings
  - DAQ Controls:
    - Start and stop buttons which run `daq.py` in the background
    - Name input box (to specify the DAQ output file name)
    - Configuration file dropdown selection menu
    - Configuration file display
  - Device Controls:
    - Set and stop buttons which run `controller.py` in the background
    - Device dropdown selection menu
    - Quantity dropdown selection menu
    - `Value`: value to set the quantity to
    - `Step`: step size by which to increment the current value to get to the target
    - `Time`: amount of time between each step (in seconds)
  - DAQ Log:
    - Log of the last running `daq.py` process

![kapton_daq](https://francois-drielsma.github.io/kapton_daq/kapton_daq.png)

### Execute the DAQ standalone

Simply run

```bash
python3 daq.py --name NAME --config config/config_TAG.json
```
and it will save the data as a CSV file to
```bash
data/(date)_NAME.csv
```
For more information about the available arguments, run
```bash
python3 daq.py -h
```

### Exectute the device controller standalone

Simply run

```bash
python3 controller.py --device DEVICE --quantity QUANTITY --value VALUE --step STEP --time TIME
```
and it will set the QUANTITY of DEVICE to VALUE by increments of STEP every TIME seconds.

### Build a configuration file

Several examples of working configuration files are provided
in the `config` directory. Each configuration file is a
dictionary expressed in the YAML file-format which contains:
  - `sampling_time`: amount of time to run the DAQ
  - `refresh_rate`: frequency at which to acquire data
  - `output_name`: name of the data file to be produced
  - `instruments`: dictionary of instruments each containing
    - `type`: `IK` instrument type (e.g. `multimeter`, `power_supply`, etc.)
    - `make`: `IK` instrument maker (e.g. `fluke`, `hp`, etc.)
    - `model`: `IK` instrument model (e.g. `Fluke3000`, `HPe3631a`, etc.)
    - `comm`: `IK` communication protocol
      - `type`: protocol type (e.g. `serial`, `file`, etc.)
      - `args`: protocol parameters
    - `measurements`: dictionary of measurements to take, each containing:
      - `quantity`: `IK` quantity to measure (e.g. `voltage_dc`, `temperature`, etc.)
      - `unit`: `quantities` unit of measurement (e.g. `millivolt`, `kelvin`, etc.)
      - `name`: name of the variable to measure (CSV output column name)
      - `value` (optional): sets initial value of measurement (if power supply or virtual)
      - `channel` (optional): specifies power supply channel id

### Draw the output separately

Simply run

```bash
python3 draw_data.py data/(date)_NAME.csv
```
and it will save the plots as
```bash
output/(date)_NAME_(measurement).pdf
```
