#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/003: Unicode Based Lexical Analyzis (Using IBM's ICU Library)"
    echo "CHOICES:  BPC=2, BPC=2_NDEBUG, BPC=4, BPC=4_NDEBUG, BPC=wchar_t;"
    echo "SAME;"
    exit
fi

case $1 in
"BPC=2" )        args="BYTES_PER_CHARACTER=2         DSWITCH_ASSERTS=-DQUEX_OPTION_ASSERTS" ;;
"BPC=2_NDEBUG" ) args="NDEBUG BYTES_PER_CHARACTER=2  DSWITCH_ASSERTS=-DQUEX_OPTION_ASSERTS_DISABLED" ;;
"BPC=4" )        args="BYTES_PER_CHARACTER=4         DSWITCH_ASSERTS=-DQUEX_OPTION_ASSERTS" ;;
"BPC=4_NDEBUG" ) args="NDEBUG BYTES_PER_CHARACTER=4  DSWITCH_ASSERTS=-DQUEX_OPTION_ASSERTS_DISABLED" ;;
"BPC=wchar_t" )  args="BYTES_PER_CHARACTER=wchar_t   DSWITCH_ASSERTS=-DQUEX_OPTION_ASSERTS" ;;
esac

cd ../003  
make clean >& /dev/null
make CONVERTER=icu lexer $args >& tmp.txt
cat tmp.txt | awk '(/[Ww][Aa][Rr][Nn][Ii][Nn][Gg]/ || /[Ee][Rr][Rr][Oo][Rr]/) && ! /ASSERTS/ && ! /deprecated since quex/'
rm tmp.txt

# valgrind ./lexer >& tmp.txt
# python ../TEST/show-valgrind.py
./lexer
# echo "ICU Version 4.2 causes memory leaks."

make clean >& /dev/null
