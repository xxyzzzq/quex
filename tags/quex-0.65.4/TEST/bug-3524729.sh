#! /usr/bin/env bash
bug=3524729
if [[ $1 == "--hwut-info" ]]; then
    echo "sbellon: $bug 0.62.4 token_type distinct members cause overloading error"
    exit
fi

tmp=`pwd`
cd $bug/ 
echo Generate token class _______________________________________________
quex -i token_type.qx --token-class-only --debug-exception
echo Compile -- No output is good output ________________________________
g++ -I$QUEX_PATH Lexer-token.cpp -c >& tmp.txt
cat tmp.txt
rm -f Lexer* tmp.txt
cd $tmp
