#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Other Compilers than g++: Intel's icpc;"
    echo "CHOICES:  000, 001, 002, 003, 005, 006"
    exit
fi
source /opt/intel/composerxe-2011.2.137/bin/compilervars.sh ia32
source core.sh $1 DEBUG COMPILER=icpc
