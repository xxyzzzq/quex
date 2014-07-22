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
# (C) Frank-Rene Schaefer
#______________________________________________________________________________

if [[ $1 == "--hwut-info" ]]; then
    echo "Consistency: Files in multi.i are not included elsewhere."
else
file_multi_i=$QUEX_PATH/quex/code_base/multi.i
file_list_else=$(find $QUEX_PATH/quex/code_base -type f | grep -v '\(\.svn\)\|\(Makefile\)\|\(TEST\)\|\(multi\.i\)')

function get_included_files() {
    cat $1 | awk ' /^\# *include/ { gsub("<", "", $2); gsub(">", "", $2); gsub("\"","",$2); print $2; }'
}

included_in_multi_i=$(get_included_files $file_multi_i)
cr='
'

echo "#List of files which include files from multi.i:"
echo "#-----------------------------------------------------"
echo "# (No output is good output)"
set i=0
for file in $file_list_else; do
    file_list_included=$(get_included_files $file)
    for candidate in $included_in_multi_i; do
        if [[ $file_list_included =~ $candidate ]]; then
            echo "$(readlink -e $file)"
            echo "# --> $candidate"
        fi
    done 
    ((i+=1))
done
echo "Terminated: Considered $i files."
fi
