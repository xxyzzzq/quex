#!/bin/sh
#
quex -i uXa.qx -o Lexer --token-prefix QUEX_UUID_ --token-id-uninitialized 1114112 --token-id-termination 1114113 --token-offset 1114114 --token-policy queue --icu -b 2 --nsacc --ttnttc
g++ -o uXa uXa.cpp Lexer.cpp -I$QUEX_PATH -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED -DQUEX_OPTION_TOKEN_STAMPING_WITH_LINE_AND_COLUMN $(icu-config --cppflags) $(icu-config --ldflags) 
