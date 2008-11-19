#! /usr/bin/env bash
bug=2276285
if [[ $1 == "--hwut-info" ]]; then
    echo "marcoantonelli: $bug Memory leak when input file is not found"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
