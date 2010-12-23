#! /usr/bin/env bash
bug=3142578
if [[ $1 == "--hwut-info" ]]; then
    echo "ollydbg: $bug Output token identifier definition"
    exit
fi

tmp=`pwd`
cd $bug/ 

echo "One TokenID _________________________________________"
quex -i 1.qx -o Simple

echo "No TokenID implicitly defined _______________________"
quex -i 2.qx -o Simple

echo "Three TokenIDs ______________________________________"
quex -i 3.qx -o Simple

# cleansening
rm Simple*
cd $tmp
