#! /usr/bin/env bash
bug=1905768
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.22.9 doesn't create analyzer function for event only modes"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple --debug-exception
cat Simple.cpp | awk ' /analyzer_function/ { print; } '

# cleansening
rm -f Simple Simple.cpp Simple-*
cd $tmp
