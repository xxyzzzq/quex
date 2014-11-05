#! /usr/bin/env bash
bug=1891254
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug Lone ? as regex does not give an error in 0.19.9"
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
rm lexer*
cd $tmp
