#! /usr/bin/env bash
bug=2087087
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.31.1 --set-by switches suppress command error diagnostics"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
