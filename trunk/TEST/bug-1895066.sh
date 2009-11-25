#! /usr/bin/env bash
bug=1895066
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.20.8 #line directive after header contents missing"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple

echo
echo 'Output from constructed header:_______________________________________'
echo
cat Simple | grep -sHne '\#line'

# cleansening
rm -f Simple Simple.cpp Simple-*
cd $tmp
