#rm `find ./quex -name "*.pyc"`
#rm `find ./quex -name "*~"`
find $1/quex $1/demo -type f > __tmp.txt
find $1 -maxdepth 1 -type f >> __tmp.txt


awk ' ! /\/\.svn/ { print; }' __tmp.txt > ___tmp.txt
awk ' ! /\/TEST\// { print; }' ___tmp.txt > tmp.txt

rm __tmp.txt ___tmp.txt
