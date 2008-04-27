#! /usr/bin/env bash
bug=1952133
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug 0.24.11 Crash in Buffer Handling with tiny buffer size"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token-ids Simplism
cd $tmp
