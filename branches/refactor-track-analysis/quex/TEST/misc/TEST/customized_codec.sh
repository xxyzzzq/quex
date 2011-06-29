#! /usr/bin/env bash

case $1 in
    --hwut-info)
        echo "Customized codec files (option --codec-file);"
        ;;

    *)
        rm -f Simple*
        quex -i           customized_codec.qx  \
             --codec-file customized_codec.dat \
             -o           Simple
        awk '/customized_codec/' Simple-*customized_codec*
        rm -f Simple*
        ;;
esac
