#! /usr/bin/env bash
bug=3164355
if [[ $1 == "--hwut-info" ]]; then
    echo "inhenriksen: $bug C with whitespace character gives bad exception"
    exit
fi

tmp=`pwd`
cd $bug/ 
echo "No output is good output"
quex -i error.qx -o Simple
rm -f Simple*
cd $tmp
