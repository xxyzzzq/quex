#! /usr/bin/env bash
bug=1890876
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug {} handled oddly in define blocks in 0.19.9"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx 
cd $tmp
