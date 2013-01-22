#! /usr/bin/env bash
bug=1885855
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug P{ ...} syntax does not work outside of [:...:]"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx --debug-exception
rm Lexer*
cd $tmp
