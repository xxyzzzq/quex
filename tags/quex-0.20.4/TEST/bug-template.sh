#! /usr/bin/env bash
bug=BUG_ID
if [[ $1 == "--hwut-info" ]]; then
    echo "SUBMITTER: $bug TITLE"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx 
cd $tmp
