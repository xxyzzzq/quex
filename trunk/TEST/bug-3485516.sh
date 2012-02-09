#! /usr/bin/env bash
bug=3485516
if [[ $1 == "--hwut-info" ]]; then
    echo "clemwang: $bug 0.60.1 0.60.1 Exception Handling Disorder"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i uuu.qx --engine UuuLexer --token-prefix UUU_TKN_ 2>&1

cd $tmp
