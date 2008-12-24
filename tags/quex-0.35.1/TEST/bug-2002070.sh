#! /usr/bin/env bash
bug=2002070
if [[ $1 == "--hwut-info" ]]; then
    echo "attardi: $bug Output buffer overflow"
    exit
fi

tmp=`pwd`
cd $bug/ 
make 
./a.out text.345
# cleansening
make clean
cd $tmp
