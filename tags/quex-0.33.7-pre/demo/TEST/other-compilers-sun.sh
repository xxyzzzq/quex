#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Other Compilers than g++: Sun Microsystem's sunCC"
    echo "CHOICES:  000, 001, 002, 003, 005, 006"
    exit
fi
export TOOLPATH=/opt/sun/sunstudio
echo "##" $1
source core.sh $1 DEBUG COMPILER=/opt/sunstudio/sunstudioceres/bin/sunCC
