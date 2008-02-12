#! /usr/bin/env bash
bug=1890828
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.19.9 crashes trying to call error handler in several cases"
    exit
fi

tmp=`pwd`
cd $bug/ 
echo "(1)"
quex -i error.qx 
echo
echo "(2)"
quex -i error-2.qx 
echo
cd $tmp
