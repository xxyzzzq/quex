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
echo "-- Update Version Information"
awk -v version="'$1'" ' ! /^QUEX_VERSION/ { print; } /^QUEX_VERSION/ { print "QUEX_VERSION =",version; }' \
    ./quex/DEFINITIONS.py > tmp-DEFINITIONS.txt
mv tmp-DEFINITIONS.txt ./quex/DEFINITIONS.py

# (*) Collect the list of files under concern
echo "-- Collect files for distribution"
input=/tmp/file-list-in.txt
output=/tmp/file-list-out.txt

cd $QUEX_PATH
cd ..

find trunk/quex $directory/demo  -type f  > $input
echo "trunk/LPGL.txt" >> $input
echo "trunk/COPYRIGHT.txt" >> $input
echo "trunk/README" >> $input
echo "trunk/unit_test_results.txt" >> $input
echo "trunk/quex-exe.py" >> $input
echo "trunk/quex.bat" >> $input
echo "trunk/__init__.py" >> $input


# -- filter out all files that are not directly required for 
#    a working application.
echo "-- Filter out redundant files"
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

# -- create tar file for ./trunk
echo "-- Snapshot"
tar cf /tmp/quex-$1.tar `cat $output`
echo `ls -lh /tmp/quex-$1.tar`

# -- change base directory from ./trunk to ./quex-$version
echo "-- Place snapshot in temporary directory"
cd /tmp/
tar xf quex-$1.tar
rm quex-$1.tar 
mv trunk quex-$1

echo "-- Create tar and zip file"
tar cf quex-$1.tar ./quex-$1
zip -r quex-$1.zip ./quex-$1

# -- create xml file for the install builder
$QUEX_PATH/make_install_builder_script.py `pwd`/quex-$1 $1

# -- compress the tar file
echo "-- Further compress .tar --> 7z and gzip"
7z   a  quex-$1.tar.7z quex-$1.tar
gzip -9 quex-$1.tar

# (*) clean up
rm $input $output

echo "-- Files are ready in /tmp"
cd $orig_directory

# (*) make sure that the new version information is checked in
echo "-- Update repository / Create tag for $1"
svn commit -m "Version Info / Prepare Release $1"

# (*) branch on sourceforge subversion
svn copy https://quex.svn.sourceforge.net/svnroot/quex/trunk \
         https://quex.svn.sourceforge.net/svnroot/quex/tags/quex-$1 \
         -m "Release $1"

