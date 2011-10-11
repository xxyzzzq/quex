#! /usr/bin/env bash

case $1 in
    --hwut-info)
        echo "Test code comments;"
        ;;

    *)
        quex -i comment.qx -o WithOut 
        quex -i comment.qx -o With   \
             --comment-state-machine \
             --comment-mode-patterns \
             --comment-transitions   \
             --debug-exception
        diff With.cpp WithOut.cpp | awk ' (/</ || />/) && ! /\#/ '
        rm -f With*
        ;;
esac
