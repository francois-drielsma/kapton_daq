## Package description

Package that centralizes all the resources necessary to setup the data
acquisition for the Kapton resistivity measurement at cryogenic temperatures

## Install the InstrumentKit repository

1. Pull the repository

```
        git clone https://github.com/Galvant/InstrumentKit
```

2. Install the package

```
        cd InstrumentKit/
        python setup.py install
```
or
```
        cd InstrumentKit/
        python3 setup.py install
```

## Enable serial connections

1. Add yourself as user of the tty and dialout groups

```
	sudo adduser user tty
	sudo adduser user dialout
``` 

2. Reboot the computer

## Enable USBTMC devices

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

