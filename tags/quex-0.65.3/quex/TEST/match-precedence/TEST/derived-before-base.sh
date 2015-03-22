#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Precedence: Derived before Base;"
    exit
fi
quex -i data/derived-before-base.qx -o Simple --token-id-prefix T_  --token-policy single --debug-exception
g++ -I$QUEX_PATH -I. \
    -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
    $QUEX_PATH/TEST/lexer-simply.cpp Simple.cpp -o lexer  \
    -DQUEX_TKN_TERMINATION=T_TERMINATION
./lexer data/derived-before-base.txt 2> tmp.txt
cat tmp.txt
rm -f tmp.txt
rm -f ./lexer
rm -f Simple*
