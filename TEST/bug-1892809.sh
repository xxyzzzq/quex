#! /usr/bin/env bash
bug=1892809
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.20.4 \\x, \\X, \\U accept too many digits"
    echo "HAPPY: Simple.c:[0-9]+:;"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i error.qx -o Simple --language C --token-policy single
gcc -I./ -I$QUEX_PATH Simple.c ../lexer.c -o lexer \
    -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED

echo "(1)"
./lexer example.txt 2> tmp.txt
cat tmp.txt
rm -f tmp.txt

echo "(2)"
./lexer example-2.txt 2> tmp.txt
cat tmp.txt
rm -f tmp.txt

#
rm -f Simple* lexer
cd $tmp
