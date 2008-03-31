#! /usr/bin/env bash
bug=1892227
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug accepted as identifiers in def"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx 
cd $tmp
