#! /usr/bin/env bash
# template_file = $1
# source_file   = $2

sed  's/\$\$LEXER_CLASS_NAME\$\$/my_tester/g' $1 > tmp.txt
sed  's/inline //g' tmp.txt > tmp2.txt
echo "#include <my_tester.h>" > $2
echo "#include <cassert>" >> $2
echo "#line 1 \"$1\"" >> $2
cat  tmp2.txt >> $2
rm tmp.txt tmp2.txt
