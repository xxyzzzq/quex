#! /usr/bin/env bash
bug=2262537
if [[ $1 == "--hwut-info" ]]; then
    echo "marcoantonelli: $bug (feature) Allow Nothing is fine in define section"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
