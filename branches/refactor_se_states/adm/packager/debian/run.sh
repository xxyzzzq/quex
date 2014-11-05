#!/bin/bash
#
#Usage example:
# sudo ./run.sh   0.37.1  0
#
# ASSUMPTION: -- sources have been copied to /tmp/quex-$VERSION
#             -- /tmp/quex-packages exists
#
# ORIGINAL AUTHOR: Joaquin Duo, joaduo at users sourceforge net
# MODIFIED BY:     Frank-Rene Schaefer, fschaef at users sourceforge net
#
#-----------------------------------------------------------------------
VERSION=$1
PACKAGE_VERSION=$2

#Config
BIN_DIRECTORY='/usr/local/bin'

#sudo does not seem to inherit path files
QUEX_PATH=/home/fschaef/prj/quex/trunk/

if [[ $# < 1 ]]; then
    echo "Please, review the text content of this script for usage information."
    exit 1
fi
if [[ $# == 1 ]]; then
    PACKAGE_VERSION="0"
fi

#Create the variables after checking the inputs
base_dir=/tmp/quex-$VERSION
template_dir=$QUEX_PATH/adm/packager/debian/scripts/
package_dir=/tmp/"quex_$VERSION-$PACKAGE_VERSION""_all"

# Check assumption that sources are copied to /tmp/quex-$VERSION
if test ! -e $base_dir; then
# else
    echo "/tmp/quex-$VERSION must exist before calling this script."
    exit 1
fi

#Create the package_dir with the DEBIAN control directory
mkdir -p $package_dir/DEBIAN

# Update the version and package information in:
#  -- control file
#  -- post install file
#  -- pre-remove file
#  -- post remove file
BIN_DIRECTORY_REPLACE=$( echo $BIN_DIRECTORY | sed 's/\//\\\//g')
scripts="control preinst postinst prerm postrm copyright"
for script in $scripts; do
      sed "s/##QUEX_VERSION/$VERSION/" $template_dir/$script | \
      sed "s/##PACKAGE_VERSION/$PACKAGE_VERSION/" | \
      sed "s/##BIN_DIRECTORY/$BIN_DIRECTORY_REPLACE/"  > \
      $package_dir/DEBIAN/$script
      chmod 0755 $package_dir/DEBIAN/$script
done

#Copy the manpage into manpage.*
cp $base_dir/doc/manpage/quex.1 $package_dir/DEBIAN/manpage.1

#Copy sources to the new destination on package
mkdir -p $package_dir/opt/quex/quex-$VERSION
sudo cp -a $base_dir/* $package_dir/opt/quex/quex-$VERSION

#Set file owners
#Need to be root for this by now, later ill use fakeroot
sudo chown root:root -R $package_dir/opt

# Create the package
sudo dpkg-deb -b $package_dir

# Make package accessible 
sudo chmod 777 /tmp/*.deb 

sudo mv $package_dir.deb /tmp/quex-packages/
exit 0
