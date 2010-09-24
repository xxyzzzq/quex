#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Bad character detection.;"
    echo "CHOICES: default, customized;"
    exit
fi

quex -i src/bad-$1.qx -o EasyLexer --language C
g++ -I$QUEX_PATH -I. EasyLexer.c $QUEX_PATH/demo/C/example.c -o lexer -DPRINT_TOKEN \
     -DQUEX_SETTING_BUFFER_SIZE=10 \
     -DQUEX_OPTION_INFORMATIVE_BUFFER_OVERFLOW_MESSAGE

./lexer data/bad.txt > out.txt 2> err.txt

cat out.txt err.txt


rm -f ./EasyLexer*
rm -f ./lexer
rm -f out.txt err.txt
