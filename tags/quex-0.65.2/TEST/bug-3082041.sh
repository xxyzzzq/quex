#! /usr/bin/env bash
bug=3082041
if [[ $1 == "--hwut-info" ]]; then
    echo "fschaef: $bug 0.52.4 Buffer Memory Size not Accepted"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i simple.qx -o EasyLexer
g++ -I$QUEX_PATH -I. test.cpp EasyLexer.cpp -o test -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED -DQUEX_SETTING_BUFFER_SIZE=512 -Wall -Werror >& tmp.txt
cat tmp.txt

valgrind --leak-check=full ./test >& tmp.txt
python ../show-valgrind.py

rm tmp.txt

# cleansening
rm -f EasyLexer*
rm -f test
cd $tmp
