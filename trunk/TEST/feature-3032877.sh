#! /usr/bin/env bash
bug=3032877
if [[ $1 == "--hwut-info" ]]; then
    echo "alexeevm: $bug -b, --bytes-per-trigger enhancement"
    echo "CHOICES: normal, icu, iconv, codec;"
    exit
fi

tmp=`pwd`
cd $bug/ 

for option in {1,2,4,u8,u16,u32,uint8_t,uint16_t,uint32_t,UChar,wchar_t,3,nonsense}; do
    echo "OPTION: $option _______________________________________________________"
    echo
    quex -i simple.qx -o EasyLexer -b $option
    awk ' /QUEX_TYPE_CHARACTER/ && /define/ && !/SETTING/ ' EasyLexer-configuration
    rm -f EasyLexer*
    echo
done

cd $tmp
