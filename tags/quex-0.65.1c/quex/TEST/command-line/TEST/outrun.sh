#! /usr/bin/env bash

case $1 in
    --hwut-info)
        echo "Detect lower prio-patterns outrun higher-prio patterns;"
        echo "HAPPY: outrun.qx:[0-9]+:;"
        ;;

    *)
        quex -i outrun.qx -o Lexer --token-id-prefix TKN_ --woo --debug-exception
        rm -f Lexer*
        ;;
esac
