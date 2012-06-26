#! /usr/bin/env bash

case $1 in
    --hwut-info)
        echo "Disable several error messages.;"
        ;;

    *)
        echo No output is good output
        quex -i no-error-flags.qx -o Lexer         \
             --token-id-prefix T_                  \
             --no-error-on-dominated-pattern       \
             --no-error-on-special-pattern-subset  \
             --no-error-on-special-pattern-outrun  \
             --no-error-on-special-pattern-same    
        rm -f Lexer*
        ;;
esac
