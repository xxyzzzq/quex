#! /usr/bin/env bash
bug=patch-16
if [[ $1 == "--hwut-info" ]]; then
    echo "eabrams: $bug Compile error when indentation based without token queue"
    exit
fi

pushd $bug/ >& /dev/null
make clean >& /dev/null
echo No error output is good output
make 2>&1 > tmp.txt
../quex_pathify.sh tmp.txt

# cleansening
make clean >& /dev/null
popd >& /dev/null
