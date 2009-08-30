#! /usr/bin/env bash
bug=1948456
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug (feature) Inheritance Info"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i simple.qx -o Simple
awk ' /*\// { exit; } // { print; } ' Simple-core-engine.cpp

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simple-configuration
cd $tmp
