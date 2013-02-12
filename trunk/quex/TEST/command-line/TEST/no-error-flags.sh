#! /usr/bin/env bash

case $1 in
    --hwut-info)
        echo "Disable several error messages.;"
        ;;

    *)
        echo No output is good output
        quex -i no-error-flags.qx -o Lexer         \
             --token-id-prefix T_                  \
             --suppress 2 3 4 5 
        rm -f Lexer*
        ;;
esac
