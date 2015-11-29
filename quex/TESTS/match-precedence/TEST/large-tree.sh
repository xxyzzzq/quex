#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Precedence: Larger Inheritance Tree;"
    exit
fi
quex -i data/large-tree.qx -o Simple --token-id-prefix T_ --debug-exception
g++ -I$QUEX_PATH -I. \
    -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
    $QUEX_PATH/TEST/lexer.cpp Simple.cpp -o lexer  \
    -DQUEX_TKN_TERMINATION=T_TERMINATION
./lexer data/large-tree.txt
rm -f ./lexer
rm -f Simple*
