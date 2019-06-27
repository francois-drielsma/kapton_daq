## Package description

Package that centralizes all the resources necessary
to setup the data acquisition for the Kapton sheet
resistance measurement at cryogenic temperatures

## Prerequisites

This package is written in Python 3.

The following packages must be installed:

```
    pip3 install plotly dash dash_daq pandas numpy
```

## Install the InstrumentKit repository

The InstrumentKit package supports communications through
a variety of protocols (GPIB, RS232, USBTMC, etc.)

1. Pull the repository

```
    git clone https://github.com/francois-drielsma/InstrumentKit
```

2. Install the package

```
    cd InstrumentKit/
    python3 setup.py install
```

### Enable serial connections

1. Add yourself as user of the tty and dialout groups

```
    sudo adduser user tty
    sudo adduser user dialout
``` 

2. Reboot the computer

### Enable USBTMC devices

1. Connect the device and identify its vendor and model ID:

```
    lsusb
    Bus 001 Device 016: ID 05e6:6500 Keithley Instruments 
```

2. Add udev rules to handle the device

```
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

```
    sudo addgroup usbtmc
    sudo adduser user usbtmc
```

4. Reboot the computer

## Use the live DAQ

Simply run

```
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
   - Start and stop button which run `daq.py` in the background
   - Name input box (to specify the DAQ output file name)
   - Configuration file selector
   - Configuration file display
 - Virtual Controls:
   - Set the value of virtual devices

![kapton_daq](https://francois-drielsma.github.io/kapton_daq/kapton_daq.png)

### Execute the DAQ standalone

Simply run

```
    python3 daq.py --name NAME --config config/config_xxxxx.json
```
and it will save the data as a CSV file to
```
    data/(date)_NAME.csv
```
For more information about the available arguments, run
```
    python3 daq.py -h
```

### Draw the output separately

Simply run

```
    python3 draw_data.py data/(date)_kapton_daq.csv
```
and it will save the plots as
```
    output/(date)_(measurement).pdf
```
