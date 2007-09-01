#rm `find ./quex -name "*.pyc"`
#rm `find ./quex -name "*~"`
find ./quex/quex/ ./quex/demo -type f > tmp.txt
find ./quex -maxdepth 1 -type f       >> tmp.txt


awk ' ! /\/\.svn/ { print; }' tmp.txt
