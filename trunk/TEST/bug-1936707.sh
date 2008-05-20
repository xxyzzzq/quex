#! /usr/bin/env bash
bug=1936707
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.24.10 --plot flag doesnt seem to work"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token-ids Simplism
cd $tmp
