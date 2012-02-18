#! /usr/bin/env bash
case $1 in
    --hwut-info)
        echo "Analyzer State Tracer;"
        ;;

    *)
        quex -i debug_show.qx -o Simple \
             --path-compression-uniform \
             --template-compression \
             --template-compression-min-gain 0 -\
             --language C --debug-exception \
             --token-policy single
        gcc -I$QUEX_PATH Simple.c $q/TEST/lexer.c -I. -DQUEX_OPTION_DEBUG_SHOW -DQUEX_SETTING_BUFFER_SIZE=15 -o debug_show
        ./debug_show debug_show.txt 2>&1 | sed -e 's/:[0-9]\+:/:LineNumber:/g'
        echo rm ./debug_show Simple*
        ;;
esac

