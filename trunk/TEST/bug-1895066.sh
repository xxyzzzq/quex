#! /usr/bin/env bash
bug=1895066
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.20.8 #line directive after header contents missing"
    echo "HAPPY: line [0-9]+;"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

echo
echo 'Output from constructed header:_______________________________________'
echo
../quex_pathify.sh Simple | awk '/\#/ && /line/' 

# cleansening
rm -f Simple Simple.cpp Simple-*
cd $tmp
