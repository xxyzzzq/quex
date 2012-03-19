#! /usr/bin/env bash
bug=2277660
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug character count pre-determination"
    exit
fi

tmp=`pwd`
cd $bug/ 
bash ../test_that_it_does_not_take_too_long.sh tokenizer.qx 120


rm -f Lexer-token
# cleansening
cd $tmp
