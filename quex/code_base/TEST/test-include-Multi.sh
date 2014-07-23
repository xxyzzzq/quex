#! /usr/bin/env bash
#
# PURPOSE: The file 'multi.i' includes implementations of which are the same for
#          all lexical analyzers. To handle single and multiple lexical analyzer
#          linking effectively, it is essential that implementations done in
#          'multi.i' are not placed somewhere else.
#
# This file checks that no file included in multi.i is included in any other 
# file.
#
# Also, it checks that inside the code base 'multi.i' is only included from 
# 'single.i'.
#
# (C) Frank-Rene Schaefer
#______________________________________________________________________________

if [[ $1 == "--hwut-info" ]]; then
    echo "Consistency: Files in multi.i are not included elsewhere."
    echo "HAPPY: [0-9]+\\ files;"
else
file_multi_i=$QUEX_PATH/quex/code_base/multi.i
file_list_else=$(find $QUEX_PATH/quex/code_base -type f | grep -v '\(\.svn\)\|\(Makefile\)\|\(TEST\)\|\(multi\.i\)')

function get_included_files() {
    cat $1 | awk 'BEGIN { FS="include"; } /^\# *include/ { gsub("<", "", $2); gsub(">", "", $2); gsub("\"","",$2); print $2; }'
}

included_in_multi_i=$(get_included_files $file_multi_i)
file_list_including_multi_i=

echo "#List of files which include files from multi.i:"
echo "#-----------------------------------------------------"
echo "# (No output is good output)"
set i=0
for file in $file_list_else; do
    file_list_included=$(get_included_files $file)
    # (1) Check whether one of the included files is from the files included
    #     in 'multi.i'.
    for candidate in $included_in_multi_i; do
        if [[ $file_list_included =~ $candidate ]]; then
            echo "$(readlink -e $file)"
            echo "# --> $candidate"
        fi
    done 
    #echo "--- $file"
    #echo "--> $file_list_included"
    # (2) Check whether multi.i is included directly
    if [[ $file_list_included =~ "quex/code_base/multi.i" ]]; then
        echo "file $(basename $file) includes multi.i"
        echo "only 'single.i' is allowed to do so."
    fi
    ((i+=1))
done
echo "Terminated: Considered $i files."
fi
