#! /usr/bin/env bash
bug=2349109
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug 0.33.5 Line and Column number counts with Set skippers;"
    echo "CHOICES: newline-skipper, non-newline-skipper;"
    exit
fi

tmp=`pwd`
cd $bug/ 
make INPUT=$1
./lexer $1.txt

# cleansening
rm -f Simple Simple-core-engine.cpp Simple.cpp Simple-token_ids Simplism
cd $tmp
