#! /usr/bin/env bash
bug=1908436
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.23.6 rule precedence reversed for identical patterns"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple #:wq--debug-exception

# cleansening
rm -f Simple  Simple.cpp Simple-token_ids Simplism
cd $tmp
