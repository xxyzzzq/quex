#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    cat << EOF
        demo/003: Byte Order Mark (BOM) Cutting;
        CHOICES:  Without, UTF8-BOM, UTF16BE-BOM;
EOF
exit
fi

case $1 in
"Without" )     export args_to_lexer="example.txt";;
"UTF8-BOM" )    export args_to_lexer="example-bom.txt";;
"UTF16BE-BOM" ) export args_to_lexer="error-bom-utf16be.txt";;
esac

# HWUT provides:
#
# $2 == FIRST if it is the first choice that is applied on 
#       this test.
# $3 == LAST  if it is the last choice.
#
# $args_to_lexer are inherited to lexer call
export args_to_make="CONVERTER=ICU bom-lexer"
export lexer_name="./bom-lexer"
source core-new.sh 003 $2 $3 


