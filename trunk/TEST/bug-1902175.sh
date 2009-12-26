#! /usr/bin/env bash
bug=1902175
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug invalid escape in character set expression crashes 0.21.12"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

# cleansening
rm -f Simple  Simple.cpp Simple-token_ids Simplism
cd $tmp
