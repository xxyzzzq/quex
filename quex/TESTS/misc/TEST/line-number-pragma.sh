#! /usr/bin/env bash

case $1 in
    --hwut-info)
        echo "Testing the implementation of line number pragmas;"
        echo "HAPPY: [0-9]+;"
        ;;

    *)
        quex -i line-number-pragma.qx -o LineNumberPragma
        cat LineNumberPragma       >  tmp.txt 
        cat LineNumberPragma-token >> tmp.txt
        cat LineNumberPragma.cpp   >> tmp.txt
        echo __________________________________________________________________
        echo Pragmas
        echo
        echo __________________________________________________________________
        echo Implementations
        echo
        for file in LineNumberPragma.cpp LineNumberPragma LineNumberPragma-token; do
            echo $file
            echo
            grep -sHIne '# *line' $file;
        done

        rm -f LineNumberPragma* tmp.txt
        ;;
esac
