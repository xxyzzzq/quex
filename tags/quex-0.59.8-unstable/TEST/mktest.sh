#! /usr/bin/env bash
#
# $1 bug id number
# $2 submitter
# $3 title
#
mkdir $1
if [[ $4 == "feature" ]]; then
    file=feature-$1.sh
else
    file=bug-$1.sh
fi

cat bug-template.sh | sed -e "s/BUG\_ID/$1/g" | sed -e "s/SUBMITTER/$2/g" | sed -s "s/TITLE/$3/g" > $file

chmod u+x $file

svn add $file
svn add $1

