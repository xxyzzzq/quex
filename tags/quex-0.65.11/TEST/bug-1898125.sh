#! /usr/bin/env bash
bug=1898125
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug invalid argument for --token-id-offset can crash 0.21.4"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple --token-id-offset 0x100
echo
quex -i error.qx -o Simple --token-id-offset 0x10f
echo
quex -i error.qx -o Simple --token-id-offset foo
echo


# cleansening
rm -f Simple*
cd $tmp
