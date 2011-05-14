#! /usr/bin/env bash
bug=3235790
if [[ $1 == "--hwut-info" ]]; then
    echo "jmarsik: 0.58.2 history effect in UCS database interface: $bug "
    exit
fi

tmp=`pwd`
cd $bug/ 

quex -i simple.qx -o Simple --language C
gcc  -I$QUEX_PATH -I. ../lexer.c Simple.c -o lexer \
     -DPRINT_TOKEN \
     -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED
./lexer


# cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ '
rm -f Simple*
rm -f ./lexer

# cleansening
cd $tmp
