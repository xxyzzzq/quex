#! /usr/bin/env bash
bug=2146712
if [[ $1 == "--hwut-info" ]]; then
    echo "yaroslav_xp: $bug (feature) output directory parameter for the command line;"
    echo "CHOICES: Normal, NotExist, NoWrite;"
    exit
fi

tmp=`pwd`
cd $bug/ 
if [[ $1 == "Normal" ]]; then
    quex -i simple.qx --output-directory a/b/c/d
    find -path "*.svn*" -prune -or -print | sort
    rm a/b/c/d/Lexer*
fi
if [[ $1 == "NotExist" ]]; then
    quex -i simple.qx --output-directory a/b/c/x
    find -path "*.svn*" -prune -or -print | sort
fi
if [[ $1 == "NoWrite" ]]; then
    chmod u-w x/y/z
    quex -i simple.qx --output-directory x/y/z
    find -path "*.svn*" -prune -or -print | sort
fi

# cleansening
rm -f Lexer.cpp Lexer-token_ids 
cd $tmp
