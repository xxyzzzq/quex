#! /usr/bin/env bash
bug=1898125
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug invalid argument for --token-offset can crash 0.21.4"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple --token-offset 0x100
echo
quex -i error.qx -o Simple --token-offset 0x10f
echo
quex -i error.qx -o Simple --token-offset foo
echo


# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
