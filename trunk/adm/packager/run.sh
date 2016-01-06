#! /usr/bin/env bash 
# PURPOSE: Creating a release of Quex
#   $1  version of the quex release
#
#   --no-repo => prevents repository update
#
# (C) 2005-2008 Frank-Rene Schaefer  fschaef@users.sourceforge.net
# 
# ABSOLUTELY NO WARRANTY
#
###########################################################################
cd ~/prj/quex/trunk
mkdir -p /tmp/quex-packages

orig_directory=$PWD
export QUEX_PATH=$PWD

DIR_INSTALLBUILDER=$HOME/bin/installbuilder-9.5.5/
INSTALLBUILDER=$DIR_INSTALLBUILDER/bin/builder
INSTALLBUILDER_OUT=$DIR_INSTALLBUILDER/output


# Temporary file for building a distribution file list
file_list0=/tmp/file-list-0.txt
file_list=/tmp/file-list-1.txt

if [[ -z $1 ]]; then
    echo "Version must be defined as first argument."
    exit
fi

pushd  demo
source make_clean.sh
hwut make clean
popd

function update_version_information()
{
    # (*) Update the version information inside the application
    cd $QUEX_PATH;
    pwd
    echo "-- Update Version Information"
    awk -v version="'$1'" ' ! /^QUEX_VERSION/ { print; } /^QUEX_VERSION/ { print "QUEX_VERSION =",version; }' \
        ./quex/DEFINITIONS.py > tmp-DEFINITIONS.txt
    mv tmp-DEFINITIONS.txt ./quex/DEFINITIONS.py;

    hwut i --no-color > unit_test_results.txt;
}

function create_man_page() {
    pushd $QUEX_PATH/doc/
    python command_line_options.py
    popd
}

function collect_distribution_file_list()
{
    sub_dir=$(basename $QUEX_PATH)

    echo "QUEX_PATH:  $QUEX_PATH"
    echo "file_list0: $file_list0"
    echo "file_list:  $file_list"
    echo "sub_dir:    $(basename $QUEX_PATH)"

    # (*) Collect the list of files under concern
    echo "-- Collect files for distribution"
    cd $QUEX_PATH/..

    find $sub_dir/quex \
         $sub_dir/demo \
         -type f  > $file_list0

    echo "$sub_dir/doc/manpage/quex.1"    >> $file_list0
    echo "$sub_dir/LGPL.txt"              >> $file_list0
    echo "$sub_dir/COPYRIGHT.txt"         >> $file_list0
    echo "$sub_dir/README"                >> $file_list0
    echo "$sub_dir/unit_test_results.txt" >> $file_list0
    echo "$sub_dir/quex-exe.py"           >> $file_list0
    echo "$sub_dir/quex.bat"              >> $file_list0
    echo "$sub_dir/__init__.py"           >> $file_list0

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
         && ! /\.a$/      \
         && ! /\.so$/     \
         && ! /\.exrc$/   \
         && ! /tmp?.txt$/ \
         && ! /tmp.txt$/  \
         && ! /\.log$/    \
         && ! /\/quex\/engine\/analyzer\/examine\/doc\// \
         && ! /\/quex\/data_base\/misc\// { print; }' $file_list0 > $file_list

    # -- create tar file for ./trunk
    echo "-- Snapshot"
    tar cf /tmp/quex-$1.tar `cat $file_list`
    echo `ls -lh /tmp/quex-$1.tar`

    # -- change base directory from ./trunk to ./quex-$version
    echo "-- Place snapshot in temporary directory"
    cd /tmp/
    tar xf quex-$1.tar 
    rm quex-$1.tar 

    # -- Rename trunk, so that it carries the name quex and version info
    rm -rf quex-$1  # make sure that the directory does not exist
    mv trunk quex-$1
}

function create_packages() 
{
    cd /tmp

    echo "Create installers for $1"

    ## We do the debian packages on our own-- thanks to Joaquin Duo.
    ## $INSTALLBUILDER build ./install-builder.xml deb
    #  The 'debian/run.sh' relies on the manpage being in 'doc/manpage/'
    echo "(It is a good idea to run this script as 'sudo' ...)"
    sudo $QUEX_PATH/adm/packager/debian/run.sh $1 0

    # -- place man page in root directory, 
    #    for source distributions.
    mv /tmp/quex-$1/doc/manpage /tmp/quex-$1/manpage
    rmdir /tmp/quex-$1/doc

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
    tar cf quex-$1.tar ./quex-$1 >& /dev/null
    zip -r quex-$1.zip ./quex-$1 >& /dev/null
    7z   a quex-$1.7z  ./quex-$1 >& /dev/null

    # -- compress the tar file
    echo "-- Further compress .tar --> 7z and gzip"
    gzip -9 quex-$1.tar          >& /dev/null
}

function validate_directory_tree()
{
    # In the past it happend multiple times that somehow other directories
    # slipped into the packages. This is a basic check that only 'quex' and 'demo'
    # are included.
    cd /tmp/quex-$1

    for d in `find -maxdepth 1 -type d`; do 
        case $d in
            .)             echo "directory .    [OK]";;
            ./demo)        echo "directory demo [OK]";;
            ./quex)        echo "directory quex [OK]";;
            ./doc)         echo "directory quex [OK]";;
            *)             echo "directory '$d' is not to be packed. Abort!"; exit;; 
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
          /tmp/quex_$1*.deb                                        \
          $INSTALLBUILDER_OUT/quex-$1*.rpm                         \
          $INSTALLBUILDER_OUT/quex-$1*windows-installer.exe        \
          $INSTALLBUILDER_OUT/quex-$1-osx-installer.app.zip        \
          $INSTALLBUILDER_OUT/quex-$1*linux-installer.run          \
          $INSTALLBUILDER_OUT/quex-$1-freebsd-installer.run        \
          $INSTALLBUILDER_OUT/quex-$1-solaris-intel-installer.run  \
          $QUEX_PATH/tmp-file-list.txt                             \
          /tmp/quex-packages

    # -- create the batch file for sftp
    scriptfile=
    cat > /tmp/quex-packages/sftp-frs.sourceforge.net.sh << EOF
RSYNC:
rsync -e ssh quex* fschaef@frs.sourceforge.net:/home/frs/project/quex/DOWNLOAD
SSH:
ssh fschaef,quex@shell.sourceforge.net  -t create
FTP:
cd uploads
put quex-$1.7z                           /home/frs/project/quex/DOWNLOAD
put quex-$1.tar.gz                       /home/frs/project/quex/DOWNLOAD
put quex-$1.zip                          /home/frs/project/quex/DOWNLOAD
put quex_$1-0_i386.deb                   /home/frs/project/quex/DOWNLOAD
put quex-$1-0.i386.rpm                   /home/frs/project/quex/DOWNLOAD
put quex-$1-windows-installer.exe        /home/frs/project/quex/DOWNLOAD
put quex-$1-linux-installer.bin          /home/frs/project/quex/DOWNLOAD
put quex-$1-osx-installer.app.zip        /home/frs/project/quex/DOWNLOAD
put quex-$1-freebsd-installer.bin        /home/frs/project/quex/DOWNLOAD
put quex-$1-solaris-intel-installer.bin  /home/frs/project/quex/DOWNLOAD
cd /home/frs/project/quex
mkdir HISTORY/OLD
cd /home/frs/project/quex/DOWNLOAD
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
    pwd

    echo "-- get unit test report"
    hwut i > unit_test_results.txt

    # make sure that the new version information is checked in
    echo "-- Update repository / Create tag for $1"
    svn ci -m "Version Info / Prepare Release $1"

    # branch on sourceforge subversion
    echo "-- copy old version from trunk to tags"
    svn copy --username=fschaef \
             svn+ssh://fschaef@svn.code.sf.net/p/quex/code/trunk \
             svn+ssh://fschaef@svn.code.sf.net/p/quex/code/tags/quex-$1 \
             -m "Release $1"
}

function clean_up() {
    cd /tmp

    # (*) clean up
    rm -f $file_list0 $file_list

    cd $orig_directory

    echo "Prepared all files in directory /tmp/quex-packages"
}

update_version_information $1

create_man_page $1

collect_distribution_file_list $1

validate_directory_tree $1

create_packages $1

collect_packages $1

if [[ "$*" != *"--no-repo"* ]]; then
    repository_update $1
fi

clean_up

