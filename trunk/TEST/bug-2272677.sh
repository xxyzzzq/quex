#! /usr/bin/env bash
bug=2272677
if [[ $1 == "--hwut-info" ]]; then
    echo "attardi: $bug range_error / character count pre-determination"
    exit
fi

tmp=`pwd`
cd $bug/ 
make

# cleansening
cd $tmp
