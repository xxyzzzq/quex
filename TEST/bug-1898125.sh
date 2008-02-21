#! /usr/bin/env bash
bug=1898125
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug invalid argument for --token-offset can crash 0.21.4"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token-ids Simplism
cd $tmp
