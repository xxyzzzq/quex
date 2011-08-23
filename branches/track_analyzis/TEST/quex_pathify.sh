# Replace occurrencies of the QUEX_PATH in the output 
# by "<<QUEX_PATH>>".
extra=`echo $QUEX_PATH | sed -e 's/\\//\\\\\\//g'`
cat $1 | sed -e "s/$extra/<<QUEX_PATH>>/g"
