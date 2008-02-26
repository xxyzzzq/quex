#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Other Compilers: Intel's C++"
    echo "CHOICES:  000, 001, 002, 003, 005, 006"
    exit
fi
source /opt/intel/cc/10.1.012/bin/iccvars.sh
source core.sh $1 DEBUG COMPILER=icpc
