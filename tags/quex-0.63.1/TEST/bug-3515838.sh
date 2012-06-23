#! /usr/bin/env bash
bug=3515838

case $1 in 
    --hwut-info)
        echo "liancheng: $bug 0.62.5 Namespace specifications cause errors"
        echo "CHOICES: Cpp, C;"
    ;;

    Cpp)
        export language='--debug-exception' 
    ;;
    C) 
        export language='--language C --debug-exception'
    ;;
esac

tmp=`pwd`
cd $bug/ 

echo
echo "Language Option: '$language'"
echo

echo quex -i test.qx -o Lexey    --token-class Tokey    --show-name-spaces $language
quex      -i test.qx -o Lexey    --token-class Tokey    --show-name-spaces $language 
echo quex -i test.qx -o ::Lexey  --token-class ::Tokey  --show-name-spaces $language
quex      -i test.qx -o ::Lexey  --token-class ::Tokey  --show-name-spaces $language
echo quex -i test.qx -o a::Lexey --token-class a::Tokey --show-name-spaces $language
quex      -i test.qx -o a::Lexey --token-class a::Tokey --show-name-spaces $language
echo quex -i test.qx -o a::Lexey --token-class b::Tokey --show-name-spaces $language
quex      -i test.qx -o a::Lexey --token-class b::Tokey --show-name-spaces $language
echo quex -i test.qx -o            x0::x1::x2::x3::x4::x5::x6::x7::x8::x9::x10::x11::x12::x13::x14::x15::x16::x17::x18::x19::x20::Lexey \
                     --token-class x0::x1::x2::x3::x4::x5::x6::x7::x8::x9::x10::x11::x12::x13::x14::x15::x16::x17::x18::x19::x20::Tokey \
                     --show-name-spaces $language
quex      -i test.qx -o            x0::x1::x2::x3::x4::x5::x6::x7::x8::x9::x10::x11::x12::x13::x14::x15::x16::x17::x18::x19::x20::Lexey \
                     --token-class x0::x1::x2::x3::x4::x5::x6::x7::x8::x9::x10::x11::x12::x13::x14::x15::x16::x17::x18::x19::x20::Tokey \
                     --show-name-spaces $language
echo quex -i test.qx -o            x0::x1::x2::x3::x4::x5::x6::x7::x8::x9::x10::x11::x12::x13::x14::x15::x16::x17::x18::x19::x20::Lexey \
                     --token-class y0::y1::y2::y3::y4::y5::y6::y7::y8::y9::y10::y11::y12::y13::y14::y15::y16::y17::y18::y19::y20::Tokey \
                     --show-name-spaces $language
quex      -i test.qx -o            x0::x1::x2::x3::x4::x5::x6::x7::x8::x9::x10::x11::x12::x13::x14::x15::x16::x17::x18::x19::x20::Lexey \
                     --token-class y0::y1::y2::y3::y4::y5::y6::y7::y8::y9::y10::y11::y12::y13::y14::y15::y16::y17::y18::y19::y20::Tokey \
                     --show-name-spaces $language

rm -f *Lexey*
rm -f *Tokey*
cd $tmp
