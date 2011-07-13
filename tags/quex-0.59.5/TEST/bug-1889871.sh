#! /usr/bin/env bash
bug=1889871
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.19.4 crashes if [] expression contains unescaped -"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx 
cd $tmp
