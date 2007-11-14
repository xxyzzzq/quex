#rm `find ./quex -name "*.pyc"`
#rm `find ./quex -name "*~"`
directory=`pwd`
directory=`basename $directory`

input=tmp_in.txt
output=tmp_out.txt
find ./quex ./demo  -type f  > $input
find ./ -maxdepth 1 -type f >> $input

# -- filter out all files that are not directly required for 
#    a working application.
awk ' ! /\/\.svn/ { print; }'  $input > $output; cp $output $input
awk ' ! /\/TEST\// { print; }' $input > $output; cp $output $input
awk ' ! /\.o$/ { print; }'     $input > $output; cp $output $input
awk ' ! /\.pyc$/ { print; }'   $input > $output; cp $output $input
awk ' ! /\.pdf$/ { print; }'   $input > $output; cp $output $input
awk ' ! /\~$/ { print; }'      $input > $output; cp $output $input
awk ' ! /\.bak$/ { print; }'   $input > $output; cp $output $input
awk ' ! /\.htm$/ { print; }'   $input > $output; cp $output $input
awk ' ! /\.html$/ { print; }'  $input > $output; cp $output $input

cat $output
rm $input $output
