#! /usr/bin/env bash
#
# $1 input file to quex
#
file=$1 # `pwd`/error.qx
max_time=$2
quex_application=$QUEX_PATH/quex-exe.py

# Start the process _________________________________________________________________
$quex_application -i $file &

# Give it a couple of seconds _______________________________________________________
time=0
while (( $time < $max_time )); do
    sleep 1  # Sleep one second
    time=$(($time+1))
    echo "## $time seconds"
    process=`ps aux | grep $file | grep $quex_application`
    if [[ -z $process ]]; then
        echo "Oll Korrekt"
        # Show the content of this directory
        ls Lexer*
        rm Lexer Lexer.cpp Lexer-token_ids Lexer-configuration
        exit
    fi
done

# get the process id ________________________________________________________________
echo "Error, generating process took to long"
i=0
for word in $process; do 
    i=$((i+1))
    if [[ $i == 2 ]]; then
        process_id=$word
        break;
    fi
done
echo $process_id
kill -15 $process_id
