#! /usr/bin/env bash
bug=1885846
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug Empty RE in define section"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i missing-regex-in-define.qx --engine Simple
cd $tmp
