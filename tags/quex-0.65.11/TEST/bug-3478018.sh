#! /usr/bin/env bash
bug=3478018
if [[ $1 == "--hwut-info" ]]; then
    echo "clemwang: $bug 0.62.3 errmsg about missing { when missing }"
    exit
fi

tmp=`pwd`
cd $bug/ 

quex -i test.qx
cd $tmp
