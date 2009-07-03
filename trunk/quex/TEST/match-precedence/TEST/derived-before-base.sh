#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Precedence: Derived before Base;"
    exit
fi
quex -i data/derived-before-base.qx -o Simple --token-prefix T_
g++ -I$QUEX_PATH -I. \
    -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
    lexer.cpp Simple-core-engine.cpp Simple.cpp -o lexer 
./lexer data/derived-before-base.txt
rm -f ./lexer
rm -f Simple*
