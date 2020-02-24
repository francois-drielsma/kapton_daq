#!/bin/bash

# Get the current directory and the base directory
CURRENT_DIR="$(pwd)"
where="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export DAQ_BASEDIR=${where}

# Set the path to the config files and device files in the base directory
unset DAQ_CFGDIR DAQ_DEVDIR
export DAQ_CFGDIR=$DAQ_BASEDIR/config
export DAQ_DEVDIR=$DAQ_BASEDIR/devices

# Set the path to the data files and log files to the current directory
unset DAQ_DATDIR DAQ_LOGDIR
export DAQ_DATDIR=$CURRENT_DIR/data
export DAQ_LOGDIR=$CURRENT_DIR/log

# Create directories if they don't yet exist
mkdir -p $DAQ_DEVDIR
mkdir -p $DAQ_DATDIR
mkdir -p $DAQ_LOGDIR

# Print the information
echo
printf "\033[93mKapton DAQ\033[00m Shell env. is necessary before running DAQ:\n"
printf "    \033[95mDAQ_BASEDIR\033[00m = $DAQ_BASEDIR\n"
printf "    \033[95mDAQ_CFGDIR\033[00m  = $DAQ_CFGDIR\n"
printf "    \033[95mDAQ_DEVDIR\033[00m  = $DAQ_DEVDIR\n"
printf "    \033[95mDAQ_DATDIR\033[00m  = $DAQ_DATDIR\n"
printf "    \033[95mDAQ_LOGDIR\033[00m  = $DAQ_LOGDIR\n"
