#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Other Compilers than g++: Intel's icpc;"
    echo "CHOICES:  000, 001, 002, 003, 005, 006"
    exit
fi
source /opt/intel/cc/10.1.018/bin/iccvars.sh
source core.sh $1 DEBUG COMPILER='icpc'
