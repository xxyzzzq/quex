#! /usr/bin/env bash
bug=265
if [[ $1 == "--hwut-info" ]]; then
    echo "sbellon: $bug Modification time change on input file."
    exit
fi

tmp=`pwd`
cd $bug/ 

file_list="token.h token_ids.h nonsense.qx derived.h codec.dat"
echo $file_list
echo

rm -f before.txt after.txt

for file in $file_list; do
    echo $file:                                            >> before.txt
    stat --printf "modified %y %Y\nchanged  %z %Z\n" $file >> before.txt
done

quex -i nonsense.qx --foreign-token-id-file token_ids.h --token-class-file token.h \
    --derived-class-file derived.h --dc Derived --codec-file codec.dat \
     -o EasyLexer --debug-exception --suppress 1 0 2>&1 

echo
for file in $file_list; do
    echo $file:                                            >> after.txt
    stat --printf "modified %y %Y\nchanged  %z %Z\n" $file >> after.txt
done

echo
echo Generated Files:
ls EasyLexer* | sort

echo
echo "Compare time stamps before and after (No Output is Good output)"
diff before.txt after.txt

rm -f EasyLexer*
rm -f before.txt after.txt
cd $tmp
