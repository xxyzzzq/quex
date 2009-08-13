#! /usr/bin/env bash
bug=1893874
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug Missing colon in mode definition crashes 0.20.5"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx 
cd $tmp
