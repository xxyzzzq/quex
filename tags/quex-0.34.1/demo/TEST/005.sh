#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "demo/005: Including Files"
    echo "CHOICES:  1, 1_NDEBUG, 2, 2_NDEBUG"
    exit
fi

case $1 in
"1" ) export args_to_lexer="example.txt"  
;;

"1_NDEBUG" ) export args_to_lexer="example.txt" 
             args="NDEBUG"
;;

"2" ) export args_to_lexer="example-2.txt" 
;;

"2_NDEBUG" ) export args_to_lexer="example-2.txt" 
             args="NDEBUG"
;;
esac

source core.sh 005 $args 

export args_to_lexer=""
