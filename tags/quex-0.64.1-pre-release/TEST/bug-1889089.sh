#! /usr/bin/env bash
bug=1889089
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug Single state mode causes quex to crash"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx 
cd $tmp
