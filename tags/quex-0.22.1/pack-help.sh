# PURPOSE: Creating a release of Quex
#   $1  version of the quex release
#
# (C) 2007 Frank-Rene Schaefer  fschaef@users.sourceforge.net
# 
# ABSOLUTELY NO WARRANTY
#
###########################################################################
#rm `find ./quex -name "*.pyc"`
#rm `find ./quex -name "*~"`
orig_directory=`pwd`
directory=`basename $orig_directory`

# (*) Update the version information inside the application
awk -v version="'$1'" ' ! /^QUEX_VERSION/ { print; } /^QUEX_VERSION/ { print "QUEX_VERSION =",version; }' \
    ./quex/DEFINITIONS.py > tmp-DEFINITIONS.txt
mv tmp-DEFINITIONS.txt ./quex/DEFINITIONS.py

# (*) Collect the list of files under concern
input=/tmp/file-list-in.txt
output=/tmp/file-list-out.txt

cd ..

find $directory/quex $directory/demo  -type f  > $input
find $directory/ -maxdepth 1 -type f >> $input

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
awk ' ! /\.swo$/ { print; }'  $input > $output; cp $output $input
awk ' ! /\.swp$/ { print; }'  $input > $output; cp $output $input
awk ' ! /trunk\/quex\/data_base\/misc\// { print; }'  $input > $output; cp $output $input

# (*) create packages: .tar.7z, .tar.gz

# -- create xml file for the install builder
$directory/make_install_builder_script.py $output $1

echo "Exit, since we only want to create the xml file."
exit
# -- create tar file for ./trunk
tar cf /tmp/quex-$1.tar `cat $output`

# -- change base directory from ./trunk to ./quex-$version
cd /tmp/
tar xf quex-$1.tar
rm quex-$1.tar 
mv trunk quex-$1
tar cf quex-$1.tar ./quex-$1

# -- compress the tar file
7z a quex-$1.tar.7z quex-$1.tar
gzip -9 quex-$1.tar

# (*) clean up
rm $input $output

echo "Files are located in /tmp"
cd $orig_directory

# (*) make sure that the new version information is checked in
svn commit ./quex/DEFINITIONS.py -m 'version info'

# (*) branch on sourceforge subversion
svn copy https://quex.svn.sourceforge.net/svnroot/quex/trunk \
         https://quex.svn.sourceforge.net/svnroot/quex/tags/quex-$1 \
         -m "Release $1"
