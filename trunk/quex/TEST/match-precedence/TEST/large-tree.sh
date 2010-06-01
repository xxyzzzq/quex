#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Precedence: Larger Inheritance Tree;"
    exit
fi
quex -i data/large-tree.qx -o Simple --token-prefix T_
g++ -I$QUEX_PATH -I. \
    -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
    lexer.cpp Simple.cpp -o lexer 
./lexer data/large-tree.txt
rm -f ./lexer
rm -f Simple*
