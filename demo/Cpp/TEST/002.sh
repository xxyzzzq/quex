#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/002: Indentation Based Scopes"
    echo "CHOICES:  NDEBUG, DEBUG, customized;"
    echo "HAPPY:    [0-9]+;"
    echo "SAME;"
    exit
fi

case $1 in 
    NDEBUG-customized)
        cd ../002
        make clean lexer2 >& /dev/null
        valgrind ./lexer2 example2.txt > tmp.txt 2>&1 

        python $QUEX_PATH/TEST/show-valgrind.py tmp.txt
        rm -f tmp.txt
        ;;
    *)
        source core-new.sh 002 $2 $3 $1
esac

