#! /usr/bin/env bash
bug=2251359
if [[ $1 == "--hwut-info" ]]; then
    echo "marcoantonelli: $bug (feature) Single-character token without name"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
