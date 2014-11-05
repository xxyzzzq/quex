#! /usr/bin/env bash
bug=2002474
if [[ $1 == "--hwut-info" ]]; then
    echo "attardi: $bug Segmentation Fault while UTF-8 Decoding"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
