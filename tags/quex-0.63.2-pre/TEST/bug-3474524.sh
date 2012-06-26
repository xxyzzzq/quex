#! /usr/bin/env bash
bug=3474524
if [[ $1 == "--hwut-info" ]]; then
    echo "clemwang: $bug 0.62.3 Escape characters in --language dot plot of [:space:]"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i simple.qx --language dot
cat ONE_AND_ONLY.dot
rm ONE_AND_ONLY.dot
cd $tmp
