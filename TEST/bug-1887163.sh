#! /usr/bin/env bash
bug=1887163
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug Single state mode causes quex to crash"
    exit
fi

tmp=`pwd`
cd $bug/ 
echo "Original Error:"
quex -i error.qx -o Simple
echo

echo "Second Use Case:"
quex -i error-2.qx -o Simple
echo

echo "Third Use Case:"
quex -i error-3.qx -o Simple # --debug-exception
echo
cd $tmp
