.. _sec:update-unicode-db:

Updating the Unicode Database
=============================

The current release of Quex comes with Unicode version 8.0. However, the it
uses the raw data files as they are released by the Unicode Consortium. This
facilitates the update to newer versions. This section describes how it is
done. 

Versions of the database are available for free and can be downloaded under
``http://www.unicode.org/Public/zipped/*version*/``. A file called "UCD.zip"
contains all required databases. Create a dedicated directory, copy the the
file into it, enter, and unzip. In a Unix-like system this corresponds to::

   > mkdir /tmp/UnicodeDb
   > mv    UCD.zip /tmp/UnicodeDb/
   > cd    /tmp/UnicodeDb/
   > unzip UCD.zip

The Unicode Database contains more files than required. Only copy the
files which are already present. Quex's Unicode Data is stored in::

   $QUEX_PATH/quex/engine/codec_db/unicode/database

With the database files stored in "/tmp/UnicodeDb/" this can be done by
the following bash script::

   > cd $QUEX_PATH/quex/engine/codec_db/unicode/database
   > for file in $(find -type f); do 
   >   cp /tmp/UnicodeDb/$file $file; 
   > done

Under other operating systems a diff-merge tool such as 'kdiff3' or
'BeyondCompare' support restricted copying of required files. If 
storage is no issue, simply copy all files to the database directory.
