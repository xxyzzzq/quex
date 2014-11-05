#! /usr/bin/env bash
bug=1889892
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug x, X or followed by a non-hex digit crashes 0.19.4"
    exit
fi

tmp=`pwd`
cd $bug/ 
echo "(1)"
quex -i error.qx 
echo "(2)"
quex -i error-1.qx 
echo "(3)"
quex -i error-2.qx 
echo "(4)"
quex -i error-3.qx 
cd $tmp
