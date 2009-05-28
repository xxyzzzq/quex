#!/bin/bash
#
#Usage example:
# sudo ./run.sh   0.37.1  0
#
# ASSUMPTION: sources have been copied to /tmp/quex-$VERSION
# 
# ORIGINAL AUTHOR: Joaquin Duo, joaduo at users sourceforge net
# MODIFIED BY:     Frank-Rene Schaefer
#
#-----------------------------------------------------------------------
VERSION=$1
PACKAGE_VERSION=$2

base_dir=/tmp/quex-$VERSION
template_dir=$QUEX_PATH/adm/packager/debian/scripts
package_dir=$base_dir/"quex_$VERSION-$PACKAGE_VERSION""_i386"

# Check assumption that sources are copied to /tmp/quex-$VERSION
if test ! -e $base_dir; then
else
    echo "/tmp/quex-$VERSION must exist before calling this script."
    exit 1
fi

if [[ $# < 2 ]]; then
    echo "Please, watch this script to see how it is executed."
    exit 1
fi
if [[ $# == 2 ]]; then
    PACKAGE_VERSION="0"
fi

# Create the new version directory

#Work on a temporal folder just in case

cp -a $template_dir/* $package_dir

# Update the version and package information in:
#  -- control file
#  -- post install file
#  -- pre-remove file
mkdir -p $package_dir/DEBIAN
for file in 'control postinst prerm'; do 
      sed "s/##QUEX_VERSION/$VERSION/" $template_dir/$file | \
      sed "s/##PACKAGE_VERSION/$PACKAGE_VERSION/" > \
      $package_dir/DEBIAN/$file
      chmod 0755 $package_dir/DEBIAN/$file
done

#Copy sources to the new destination on package
mkdir $package_dir/opt/quex/quex-$VERSION
cp -a $base_dir/* $package_dir/opt/quex/quex-$VERSION

#Set file owners
#Need to be root for this by now, later ill use fakeroot
sudo chown root:root -R $package_dir/opt
sudo chown root:root -R $package_dir/usr

#Create the package
sudo dpkg-deb -b $package_dir

#Copy the resulting package
cp temp_package/*.deb /tmp/quex-packages/

exit 0
