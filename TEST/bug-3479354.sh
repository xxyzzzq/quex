#! /usr/bin/env bash
bug=3479354
if [[ $1 == "--hwut-info" ]]; then
    echo "clemwang: $bug Reversed (right to left) Pattern Definition"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i test.qx -o EasyLexer --language C --comment-state-machine --debug-exception
awk 'BEGIN {w=0} /BEGIN:/ {w=1;} // {if(w) print;} /END:/ {w=0;}' EasyLexer.c

# cleansening
rm -f EasyLexer*
cd $tmp
