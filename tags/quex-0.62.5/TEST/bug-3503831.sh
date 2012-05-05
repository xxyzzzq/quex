#! /usr/bin/env bash
bug=3503831
if [[ $1 == "--hwut-info" ]]; then
    echo "clemwang: $bug 0.61.2 Missleading error message in anti-pattern A{foo$}"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx 2>&1

cd $tmp
