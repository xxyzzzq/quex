#! /usr/bin/env bash

if [[ $1 == "--hwut-info" ]]; then
    echo "Check that 'Lexeme' macro is not used."
    echo "HAPPY: py:[0-9]+:;"
    exit
fi

echo "The Lexeme macro does some safety checks when compiled with"
echo "QUEX_OPTION_ASSERTS. These checks are sometimes nonsense in"
echo "generated code. This test checks that no code is generated"
echo "that referes to the Lexeme macros."
echo
echo "Following lines are suppossed to be accepted:"
echo
pushd $QUEX_PATH/quex
tmp_file=$(mktemp)
# echo "|||| potpourri begin"
grep -sHIne '\(\bLexeme\b\)\|\(\bLexemeBegin\b\)\|\(\bLexemeEnd\b\)\|\(\bLexemeN\b\)' \
     . -r --exclude-dir TEST --exclude-dir .svn \
     --include "*.py" \
     | awk "! /: *#/ && ! /E_R\./ && ! /define Lexeme/ && ! /undef Lexeme/ && (/\"/ || ! /'/) " > $tmp_file

bash $QUEX_PATH/TEST/quex_pathify.sh $tmp_file | sort 

# echo "|||| potpourri end"
rm -f $tmp_file
popd
