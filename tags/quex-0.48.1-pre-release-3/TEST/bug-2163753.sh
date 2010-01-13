#! /usr/bin/env bash
bug=2163753
if [[ $1 == "--hwut-info" ]]; then
    echo "yaroslav_xp: $bug 0.32.1 Incorrect on_failure behavior"
    exit
fi

tmp=`pwd`
cd $bug/ 
make 
./a.out

# cleansening
make clean
cd $tmp
