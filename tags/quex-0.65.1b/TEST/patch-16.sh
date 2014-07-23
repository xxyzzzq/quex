#! /usr/bin/env bash
bug=patch-16
if [[ $1 == "--hwut-info" ]]; then
    echo "eabrams: $bug Compile error when indentation based without token queue"
    exit
fi

tmp=`pwd`
cd $bug/ 
echo No error output is good output
make 2>&1

# cleansening
make clean >& /dev/null
cd $tmp
