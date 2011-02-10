#! /usr/bin/env bash

case $1 in
    --hwut-info)
        echo "Test code comments;"
        ;;

    *)
        quex -i comment.qx -o WithOut 
        quex -i comment.qx -o With   \
             --comment-state-machine \
             --comment-mode-patterns
        diff With.cpp WithOut.cpp
        rm -f With*
        ;;
esac
