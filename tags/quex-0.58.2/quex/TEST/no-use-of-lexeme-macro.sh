#! /usr/bin/env bash

if [[ $1 == "--hwut-info" ]]; then
    echo "Check that 'Lexeme' macro is not used."
    exit
fi

echo "The Lexeme macro does some safety checks when compiled with"
echo "QUEX_OPTION_ASSERTS. These checks are sometimes nonsense in"
echo "generated code. This test checks that no code is generated"
echo "that referes to the Lexeme macros."
echo

grep -sHIne '\bLexeme[^N]' $QUEX_PATH/quex -r --exclude-dir .svn --exclude-dir TEST --include "*.py" | awk ' ! /define/ && ! /undef/' | sed -e 's/:[0-9]+://g'
