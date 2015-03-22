# USAGE:
#
# quex_pathify.sh filename
# quex_pathify.sh --string string
#
# Replace occurrencies of the QUEX_PATH in the output 
# by "<<QUEX_PATH>>".
#
extra=`echo $QUEX_PATH | sed -e 's/\\/$//g' | sed -e 's/\\//\\\\\\//g'`

case $1 in
    --string)
        echo $2 | sed -e "s/$extra/<<QUEX_PATH>>/g"
    ;;

    *)
        cat $1 | sed -e "s/$extra/<<QUEX_PATH>>/g"
        rm -f $1
    ;;
 esac
