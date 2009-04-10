# PURPOSE: Creating a release of Quex
#   $1  version of the quex release
#
# (C) 2005-2008 Frank-Rene Schaefer  fschaef@users.sourceforge.net
# 
# ABSOLUTELY NO WARRANTY
#
###########################################################################

cd ~/prj/quex/trunk
orig_directory=`pwd`
directory=`basename $orig_directory`

INSTALLBUILDER_OUT=/opt/installbuilder-5.4.11/output

# Temporary file for building a distribution file list
input=/tmp/file-list-in.txt
output=/tmp/file-list-out.txt


function update_version_information()
{
    # (*) Update the version information inside the application
    cd $QUEX_PATH

    echo "-- Update Version Information"
    awk -v version="'$1'" ' ! /^QUEX_VERSION/ { print; } /^QUEX_VERSION/ { print "QUEX_VERSION =",version; }' \
        ./quex/DEFINITIONS.py > tmp-DEFINITIONS.txt
    mv tmp-DEFINITIONS.txt ./quex/DEFINITIONS.py

    hwut i > unit_test_results.txt
}

function collect_distribution_file_list()
{
    cd $QUEX_PATH
    cd ..

    # (*) Collect the list of files under concern
    echo "-- Collect files for distribution"

    find trunk/quex $directory/demo  -type f  > $input

    echo "trunk/LPGL.txt"              >> $input
    echo "trunk/COPYRIGHT.txt"         >> $input
    echo "trunk/README"                >> $input
    echo "trunk/unit_test_results.txt" >> $input
    echo "trunk/quex-exe.py"           >> $input
    echo "trunk/quex.bat"              >> $input
    echo "trunk/__init__.py"           >> $input


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
    awk ' ! /\.swo$/ { print; }'   $input > $output; cp $output $input
    awk ' ! /\.swp$/ { print; }'   $input > $output; cp $output $input
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
}

function create_packages() 
{
    cd /tmp

    echo "Create installers for $1"

    # -- create xml file for the install builder
    $QUEX_PATH/adm/packager/make_install_builder_script.py `pwd`/quex-$1 $1
    /opt/installbuilder-5.4.11/bin/builder build ./install-builder.xml windows
    /opt/installbuilder-5.4.11/bin/builder build ./install-builder.xml linux
    /opt/installbuilder-5.4.11/bin/builder build ./install-builder.xml rpm
    ## We do the debian packages on our own-- thanks to Joaquin Duo.
    ## /opt/installbuilder-5.4.11/bin/builder build ./install-builder.xml deb
    $QUEX_PATH/adm/packager/debian/run.sh $1
    /opt/installbuilder-5.4.11/bin/builder build ./install-builder.xml osx
    /opt/installbuilder-5.4.11/bin/builder build ./install-builder.xml freebsd
    /opt/installbuilder-5.4.11/bin/builder build ./install-builder.xml solaris-intel

    cd $INSTALLBUILDER_OUT
    zip -r quex-$1-osx-installer.app.zip quex-$1-osx-installer.app

    echo "-- Create tar and zip file"
    cd /tmp
    tar cf quex-$1.tar ./quex-$1
    zip -r quex-$1.zip ./quex-$1

    # -- compress the tar file
    echo "-- Further compress .tar --> 7z and gzip"
    7z   a  quex-$1.tar.7z quex-$1.tar
    gzip -9 quex-$1.tar
}

function collect_packages() 
{
    rm -rf /tmp/quex-packages
    mkdir /tmp/quex-packages

    mv /tmp/quex-$1.tar.7z \
       /tmp/quex-$1.tar.gz \
       /tmp/quex-$1.zip    \
       $INSTALLBUILDER_OUT/quex_$1*.deb                         \
       $INSTALLBUILDER_OUT/quex-$1*.rpm                         \
       $INSTALLBUILDER_OUT/quex-$1*windows-installer.exe        \
       $INSTALLBUILDER_OUT/quex-$1*linux-installer.bin          \
       $INSTALLBUILDER_OUT/quex-$1-osx-installer.app.zip        \
       $INSTALLBUILDER_OUT/quex-$1-freebsd-installer.bin        \
       $INSTALLBUILDER_OUT/quex-$1-solaris-intel-installer.bin  \
       /tmp/quex-packages

    # -- create the batch file for sftp
    scriptfile=/tmp/quex-packages/sftp-frs.sourceforge.net.sh
    echo "cd uploads"         >  $scriptfile
    echo "put quex-$1.tar.7z" >> $scriptfile
    echo "put quex-$1.tar.gz" >> $scriptfile
    echo "put quex-$1.zip   " >> $scriptfile
    echo "put quex_$1-0_i386.deb  " >> $scriptfile
    echo "put quex-$1-0.i386.rpm  " >> $scriptfile
    echo "put quex-$1-windows-installer.exe " >> $scriptfile
    echo "put quex-$1-linux-installer.bin   " >> $scriptfile
    echo "put quex-$1-osx-installer.app.zip " >> $scriptfile
    echo "put quex-$1-freebsd-installer.bin " >> $scriptfile
    echo "put quex-$1-solaris-intel-installer.bin " >> $scriptfile
}

function repository_update() {
    cd $QUEX_PATH

    hwut i > unit_test_results.txt

    # make sure that the new version information is checked in
    echo "-- Update repository / Create tag for $1"
    svn commit -m "Version Info / Prepare Release $1"

    # branch on sourceforge subversion
    svn copy https://quex.svn.sourceforge.net/svnroot/quex/trunk \
             https://quex.svn.sourceforge.net/svnroot/quex/tags/quex-$1 \
             -m "Release $1"
}

function clean_up() {
    cd /tmp

    # (*) clean up
    rm $input $output

    cd $orig_directory

    echo "Prepared all files in directory /tmp/quex-packages"
}

update_version_information $1

collect_distribution_file_list $1

create_packages $1

collect_packages $1

repository_update $1

clean_up

