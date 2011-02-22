#! /usr/bin/env bash
bug=3077292
if [[ $1 == "--hwut-info" ]]; then
    echo "ymarkovitch: $bug 0.52.3 Compilation Error With DEBUG_MODE_TRANSITIONS"
    exit
fi

tmp=`pwd`
cd $bug/ 
quex -i simple.qx --language C
gcc -c lexer.c -I$QUEX_PATH -DQUEX_OPTION_DEBUG_SHOW -DQUEX_OPTION_LINE_NUMBER_COUNTING -DQUEX_OPTION_COLUMN_NUMBER_COUNTING >& tmp.txt
cat tmp.txt

echo "Confirm lexer has been created"
ls lexer.o >& tmp.txt

cat tmp.txt

# cleansening
rm tmp.txt
rm lexer*

cd $tmp
