#! /usr/bin/env bash
bug=1905768
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug "
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple
cat Simple-core-engine.cpp | awk ' /analyser_function/ { print; } '

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
