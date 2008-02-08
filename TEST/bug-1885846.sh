#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "1885846 by 'sphericalcow': Empty RE in define section"
    exit
fi

tmp=`pwd`
cd 1885846/ 
quex -i missing-regex-in-define.qx --engine Simple
cd $tmp
