echo "$1 --> $2"
grep -sl $1 `find -path "*.svn*" -prune -or -print` > tmp.txt
echo "Files:"
for file in `cat tmp.txt`; do echo "   $file";  done
perl -pi.bak -e "s/$1/$2/g" `cat tmp.txt`
for file in `cat tmp.txt`; do rm $file.bak;  done
rm tmp.txt
