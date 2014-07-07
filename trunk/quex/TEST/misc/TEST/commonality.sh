#! /usr/bin/env bash

case $1 in
    --hwut-info)
        echo "Inadmissible commonalities;"
        echo "CHOICES: indentation-newline, skip, skip_range, skip_nested_range, mix, mix2;"
        ;;

    *)
        quex -i interfere-$1.qx >& tmp.txt # --debug-exception
        cat tmp.txt
        rm tmp.txt
        ;;
esac
