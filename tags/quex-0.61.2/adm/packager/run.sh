#! /usr/bin/env bash 
# PURPOSE: Creating a release of Quex
#   $1  version of the quex release
#
# (C) 2005-2008 Frank-Rene Schaefer  fschaef@users.sourceforge.net
# 
# ABSOLUTELY NO WARRANTY
#
###########################################################################

cd ~/prj/quex/trunk
mkdir -f /tmp/quex-packages

orig_directory=`pwd`
directory=`basename $orig_directory`

INSTALLBUILDER=/opt/installbuilder-7.2.0/bin/builder
INSTALLBUILDER_OUT=/opt/installbuilder-7.2.0/output

# Temporary file for building a distribution file list
input=/tmp/file-list-in.txt
output=/tmp/file-list-out.txt

if [[ -z $1 ]]; then
    echo "Version must be defined as first argument."
    exit
fi


function update_version_information()
{
    # (*) Update the version information inside the application
    cd $QUEX_PATH;

    echo "-- Update Version Information"
    awk -v version="'$1'" ' ! /^QUEX_VERSION/ { print; } /^QUEX_VERSION/ { print "QUEX_VERSION =",version; }' \
        ./quex/DEFINITIONS.py > tmp-DEFINITIONS.txt
    mv tmp-DEFINITIONS.txt ./quex/DEFINITIONS.py;

    hwut i > unit_test_results.txt;
}

function collect_distribution_file_list()
{
    cd $QUEX_PATH;
    cd ..;

    # (*) Collect the list of files under concern
    echo "-- Collect files for distribution"

    find trunk/quex $directory/demo  -type f  > $input

    echo "trunk/LGPL.txt"              >> $input
    echo "trunk/COPYRIGHT.txt"         >> $input
    echo "trunk/README"                >> $input
    echo "trunk/unit_test_results.txt" >> $input
    echo "trunk/quex-exe.py"           >> $input
    echo "trunk/quex.bat"              >> $input
    echo "trunk/__init__.py"           >> $input


    # -- filter out all files that are not directly required for 
    #    a working application.
    echo "-- Filter out redundant files"
    awk '   ! /\/\.svn/   \
         && ! /\/TEST\//  \
         && ! /\.o$/      \
         && ! /\.pyc$/    \
         && ! /\.pdf$/    \
         && ! /\~$/       \
         && ! /\.bak$/    \
         && ! /\.htm$/    \
         && ! /\.html$/   \
         && ! /\.swo$/    \
         && ! /\.swp$/    \
         && ! /trunk\/quex\/data_base\/misc\// { print; }' $input > $QUEX_PATH/tmp-file-list.txt
    mv -f tmp.txt $input

    # -- create tar file for ./trunk
    echo "-- Snapshot"
    tar cf /tmp/quex-$1.tar `cat $QUEX_PATH/tmp-file-list.txt` 
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

    ## We do the debian packages on our own-- thanks to Joaquin Duo.
    ## $INSTALLBUILDER build ./install-builder.xml deb
    sudo $QUEX_PATH/adm/packager/debian/run.sh $1 0
    # -- create xml file for the install builder
    $QUEX_PATH/adm/packager/make_install_builder_script.py `pwd`/quex-$1 $1
    $INSTALLBUILDER build ./install-builder.xml windows
    $INSTALLBUILDER build ./install-builder.xml linux
    $INSTALLBUILDER build ./install-builder.xml rpm
    $INSTALLBUILDER build ./install-builder.xml osx
    $INSTALLBUILDER build ./install-builder.xml freebsd
    $INSTALLBUILDER build ./install-builder.xml solaris-intel

    cd $INSTALLBUILDER_OUT
    zip -r quex-$1-osx-installer.app.zip quex-$1-osx-installer.app

    echo "-- Create tar and zip file"
    cd /tmp
    tar cf quex-$1.tar ./quex-$1
    zip -r quex-$1.zip ./quex-$1
    7z   a quex-$1.7z  ./quex-$1

    # -- compress the tar file
    echo "-- Further compress .tar --> 7z and gzip"
    gzip -9 quex-$1.tar
}

function validate_directory_tree()
{
    # In the past it happend multiple times that somehow other directories
    # slipped into the packages. This is a basic check that only 'quex' and 'demo'
    # are included.
    cd /tmp/quex-$1

    for d in `find -maxdepth 1 -type d`; do 
        case $d in
            .)      echo "directory .    [OK]";;
            ./demo) echo "directory demo [OK]";;
            ./quex) echo "directory quex [OK]";;
            *)      echo "directory '$d' is not to be packed. Abort!"; exit;; 
        esac
    done
}

function collect_packages() 
{
    rm -rf /tmp/quex-packages
    mkdir /tmp/quex-packages

    mv -f /tmp/quex-$1.7z     \
          /tmp/quex-$1.tar.gz \
          /tmp/quex-$1.zip    \
          $INSTALLBUILDER_OUT/quex_$1*.deb                         \
          $INSTALLBUILDER_OUT/quex-$1*.rpm                         \
          $INSTALLBUILDER_OUT/quex-$1*windows-installer.exe        \
          $INSTALLBUILDER_OUT/quex-$1*linux-installer.bin          \
          $INSTALLBUILDER_OUT/quex-$1-osx-installer.app.zip        \
          $INSTALLBUILDER_OUT/quex-$1-freebsd-installer.bin        \
          $INSTALLBUILDER_OUT/quex-$1-solaris-intel-installer.bin  \
          $QUEX_PATH/tmp-file-list.txt                             \
          /tmp/quex-packages

    # -- create the batch file for sftp
    scriptfile=
    cat > /tmp/quex-packages/sftp-frs.sourceforge.net.sh << EOF
cd uploads
put quex-$1.7z                       /home/frs/project/q/qu/quex/DOWNLOAD
put quex-$1.tar.gz                       /home/frs/project/q/qu/quex/DOWNLOAD
put quex-$1.zip                          /home/frs/project/q/qu/quex/DOWNLOAD
put quex_$1-0_i386.deb                   /home/frs/project/q/qu/quex/DOWNLOAD
put quex-$1-0.i386.rpm                   /home/frs/project/q/qu/quex/DOWNLOAD
put quex-$1-windows-installer.exe        /home/frs/project/q/qu/quex/DOWNLOAD
put quex-$1-linux-installer.bin          /home/frs/project/q/qu/quex/DOWNLOAD
put quex-$1-osx-installer.app.zip        /home/frs/project/q/qu/quex/DOWNLOAD
put quex-$1-freebsd-installer.bin        /home/frs/project/q/qu/quex/DOWNLOAD
put quex-$1-solaris-intel-installer.bin  /home/frs/project/q/qu/quex/DOWNLOAD
cd /home/frs/project/q/qu/quex
mkdir HISTORY/OLD
cd /home/frs/project/q/qu/quex/DOWNLOAD
rename quex-OLD.7z                           ../HISTORY/OLD/quex-OLD.7z
rename quex-OLD.tar.gz                       ../HISTORY/OLD/quex-OLD.tar.gz
rename quex-OLD.zip                          ../HISTORY/OLD/quex-OLD.zip   
rename quex_OLD-0_i386.deb                   ../HISTORY/OLD/quex_OLD-0_i386.deb
rename quex-OLD-0.i386.rpm                   ../HISTORY/OLD/quex-OLD-0.i386.rpm 
rename quex-OLD-windows-installer.exe        ../HISTORY/OLD/quex-OLD-windows-installer.exe
rename quex-OLD-linux-installer.bin          ../HISTORY/OLD/quex-OLD-linux-installer.bin 
rename quex-OLD-osx-installer.app.zip        ../HISTORY/OLD/quex-OLD-osx-installer.app.zip
rename quex-OLD-freebsd-installer.bin        ../HISTORY/OLD/quex-OLD-freebsd-installer.bin
rename quex-OLD-solaris-intel-installer.bin  ../HISTORY/OLD/quex-OLD-solaris-intel-installer.bin 
EOF
}

function repository_update() {
    cd $QUEX_PATH;

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

validate_directory_tree $1

create_packages $1

collect_packages $1

repository_update $1

clean_up

