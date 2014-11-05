#! /usr/bin/env bash
bug=1952133
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug 0.24.11 Crash in Buffer Handling with tiny buffer size"
    echo "CHOICES: 29, 30, 127, 128, 129, 2499, 2500, 2501, 2502"
    exit
fi

tmp=`pwd`
cd $bug/ 
make clean
make BUFFER_SIZE=$1
./lexer error-example.txt 
make clean

cd $tmp
