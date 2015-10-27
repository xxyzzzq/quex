#! /usr/bin/env bash

case $1 in
    --hwut-info)
        echo "Testing the implementation of line number pragmas;"
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
        grep -sHIne '((A))' LineNumberPragma.cpp LineNumberPragma LineNumberPragma-token 

        rm -f LineNumberPragma* tmp.txt
        ;;
esac
