#! /usr/bin/env bash
bug=2395200
if [[ $1 == "--hwut-info" ]]; then
    echo "nobody: $bug assert  in QuexBufferFiller_load_forward (The StrangeStream Issue)"
    echo "CHOICES: error-lexer, lexer;"
    exit
fi

tmp=`pwd`
cd $bug/ 
make $1 >& /dev/null
./$1 >& tmp.txt
cat tmp.txt
make clean >& /dev/null

cd $tmp
