# One might want to fill 'tmp.txt' with a dedicated list of files
# to be subject to replacement. Then set $3 to --my-tmp-txt
echo "$1 --> $2"
if [[ $3 != "--my-tmp-txt" ]]; then
   grep -sl $1 `find -path "*.svn*" -prune -or -print` > tmp.txt
fi
echo "Files:"
for file in `cat tmp.txt`; do echo "   $file";  done
perl -pi.bak -e "s/$1/$2/g" `cat tmp.txt`
for file in `cat tmp.txt`; do rm -f $file.bak;  done
rm tmp.txt
