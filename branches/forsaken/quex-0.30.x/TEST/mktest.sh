mkdir $1
cat bug-template.sh | sed -e "s/BUG\_ID/$1/g" | sed -e "s/SUBMITTER/$2/g" | sed -s "s/TITLE/$3/g" > bug-$1.sh
chmod u+x bug-$1.sh
svn add bug-$1.sh
svn add $1

