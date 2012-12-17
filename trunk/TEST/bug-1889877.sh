#! /usr/bin/env bash
bug=1889877
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug '*' or '+' without prececing expression crashes 0.19.4"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx 
cd $tmp
