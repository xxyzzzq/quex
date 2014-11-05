#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Other Compilers than g++: Intel's icpc"
    echo "CHOICES:  000, 001, 002, 003, 005, 006"
    exit
fi
source /home/compilers/intel-cpp/bin/iccvars.sh
source core.sh $1 DEBUG COMPILER=icpc
