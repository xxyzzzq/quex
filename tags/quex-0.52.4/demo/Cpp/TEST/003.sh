#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    cat << EOF
        demo/003: Unicode Based Lexical Analyzis (Using GNU's Lib IConv);
        CHOICES:  BPC=2, BPC=2_NDEBUG, BPC=4, BPC=4_NDEBUG, BPC=wchar_t;
        SAME;
EOF
exit
fi

case $1 in
"BPC=2" )        args="BYTES_PER_CHARACTER=2" ;;
"BPC=2_NDEBUG" ) args="BYTES_PER_CHARACTER=2 NDEBUG" ;;
"BPC=4" )        args="BYTES_PER_CHARACTER=4" ;;
"BPC=4_NDEBUG" ) args="BYTES_PER_CHARACTER=4 NDEBUG" ;;
"BPC=wchar_t" )  args="BYTES_PER_CHARACTER=wchar_t" ;;
esac

# HWUT provides:
# $2 == FIRST if it is the first choice that is applied on this test.
# $3 == LAST  if it is the last choice.
source core-new.sh 003 $2 $3 $args 
