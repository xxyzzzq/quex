#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Indentation Counting and Range Skipper;"
    echo "CHOICES: range, range-2, nested_range;"
    exit
fi

qx_file=src/with-skip-$1.qx
txt_file=data/with-skip-$1.txt
buffer_size=1024

quex -i $qx_file -o EasyLexer --language C

gcc \
 -I$QUEX_PATH -I.                                 \
 EasyLexer.c                                      \
 $QUEX_PATH/demo/C/example.c                      \
 -o lexer -DPRINT_TOKEN                           \
 -DQUEX_SETTING_BUFFER_SIZE=$buffer_size          \
 -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED

./lexer $txt_file &> tmp.txt

cat tmp.txt

rm -f ./EasyLexer*
rm -f ./lexer
rm -f tmp.txt

