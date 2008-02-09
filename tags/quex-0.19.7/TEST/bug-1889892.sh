#! /usr/bin/env bash
bug=1889892
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug x, X or  FOLLOWED BY A NON-HEX DIGIT CRASHES 0.19.4"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx 
quex -i error-1.qx 
quex -i error-2.qx 
cd $tmp
