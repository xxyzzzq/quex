mkdir $1
cp bug-1887163.sh bug-$1.sh
chmod u+x bug-$1.sh
svn add bug-$1.sh
svn add $1

