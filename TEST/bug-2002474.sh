#! /usr/bin/env bash
bug=2002474
if [[ $1 == "--hwut-info" ]]; then
    echo "attardi: $bug Segmentation Fault while UTF-8 Decoding"
    exit
fi

tmp=`pwd`
cd $bug/ 
make 
make wiki.txt
./a.out > tmp.txt
tail --lines=20 tmp.txt

# cleansening
make clean
cd $tmp
