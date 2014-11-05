#! /usr/bin/env bash
bug=1889702
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.19.4 forbids derived modes that only add event handlers"
    exit
fi

tmp=`pwd`
cd $bug/ 
echo "(1)"
quex -i error.qx -o Simple
echo

echo "(2)"
quex -i error-2.qx -o Simple
echo

echo "(3)"
quex -i error-3.qx -o Simple
echo

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
