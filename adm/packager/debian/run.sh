#!/bin/bash
#
#7z x quex-0.37.1.tar.7z
#tar xf quex-0.37.1.tar
#rm quex-0.37.1.tar
#
#Usage example:
# sudo ./create_quex_debian_package.sh quex-0.37.1 0.37.1 0
#
SOURCES_DIRECTORY=$1
QUEX_VERSION=$2
PACKAGE_VERSION=$3

if [ "$#" != "3" ]; then
  echo "
#Usage example:
 #                                    |quex source dir         |quex version  |package version
 sudo ./create_quex_debian_package.sh  /home/quex/quex-0.37.1   0.37.1         0
  "
 exit 1
fi

#Create the new version directory
PACKAGE_DIRECTORY="quex_$QUEX_VERSION-$PACKAGE_VERSION""_i386"

#Work on a temporal folder just in case
if [ "`ls temp_package`" ]; then
  echo "
  \"temp_package\" directory exists
  remove it or rename it
  before running this script
  
  "
  exit 1
fi

mkdir temp_package

mkdir temp_package/$PACKAGE_DIRECTORY

cp -a quex_installer_TEMPLATE/Fixed/* temp_package/$PACKAGE_DIRECTORY

# Control File
sed "s/##QUEX_VERSION/$QUEX_VERSION/" quex_installer_TEMPLATE/Varying/DEBIAN/control | \
  sed "s/##PACKAGE_VERSION/$PACKAGE_VERSION/" > \
  temp_package/$PACKAGE_DIRECTORY/DEBIAN/control

#Post install file
sed "s/##QUEX_VERSION/$QUEX_VERSION/" quex_installer_TEMPLATE/Varying/DEBIAN/postinst > \
  temp_package/$PACKAGE_DIRECTORY/DEBIAN/postinst
chmod 0755 temp_package/$PACKAGE_DIRECTORY/DEBIAN/postinst

#Pre remove file
sed "s/##QUEX_VERSION/$QUEX_VERSION/" quex_installer_TEMPLATE/Varying/DEBIAN/prerm > \
  temp_package/$PACKAGE_DIRECTORY/DEBIAN/prerm
chmod 0755 temp_package/$PACKAGE_DIRECTORY/DEBIAN/prerm

#Copy sources to the new destination on package
mkdir temp_package/$PACKAGE_DIRECTORY/opt/quex/quex-$QUEX_VERSION
cp -a $SOURCES_DIRECTORY/* temp_package/$PACKAGE_DIRECTORY/opt/quex/quex-$QUEX_VERSION

#Set file owners
#Need to be root for this by now, later ill use fakeroot
sudo chown root:root -R temp_package/$PACKAGE_DIRECTORY/opt
sudo chown root:root -R temp_package/$PACKAGE_DIRECTORY/usr

#Create the package
sudo dpkg-deb -b temp_package/$PACKAGE_DIRECTORY

#Copy the resulting package
cp temp_package/*.deb ./

#Remove all the temp files
sudo rm -Rf temp_package/
# sudo rmdir temp_package

exit 0