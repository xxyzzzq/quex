X = Simple
LIB_CONV  = `icu-config --ldflags --cppflags`

# C++ Versions ________________________________________________________________
# 
lex_iconv: 
	@echo "Call to quex"
	@quex -i simple.qx -o $(X) --bet wchar_t --iconv  
	@echo "Compiling"
	g++ -I./ -I$(QUEX_PATH) \
		$(X).cpp                      \
		-Wall -Werror -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED                         \
		../lexer.cpp                     \
		-ggdb \
	   	-DQUEX_SETTING_BUFFER_SIZE=64 \
		-DPRINT_TOKEN_FIRST_NUMBER='402508 - 20' \
		-DQUEX_SETTING_ICONV_TRANSLATION_BUFFER_SIZE=64 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-o $@

lex_icu: 
	@echo "Call to quex"
	@quex -i simple.qx -o $(X) --bet wchar_t --icu  
	@echo "Compiling"
	g++ -I./ -I$(QUEX_PATH) \
		$(X).cpp                      \
		-Wall -Werror -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED                         \
		../lexer.cpp                     \
		$(LIB_CONV)                   \
		-ggdb                         \
	   	-DQUEX_SETTING_BUFFER_SIZE=64 \
		-DPRINT_TOKEN_FIRST_NUMBER='402508 - 20' \
		-DQUEX_SETTING_ICONV_TRANSLATION_BUFFER_SIZE=64 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-o $@

lex_codec: 
	@echo "Call to quex"
	@quex -i simple.qx -o $(X) --codec utf8  
	@echo "Compiling"
	g++ -I./ -I$(QUEX_PATH) \
		$(X).cpp                      \
		../lexer.cpp                     \
		-ggdb \
	   	-DQUEX_SETTING_BUFFER_SIZE=64 \
		-DPRINT_TOKEN_FIRST_NUMBER='402508 - 20' \
		-DQUEX_SETTING_ICONV_TRANSLATION_BUFFER_SIZE=64 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-DQUEX_OPTION_DEBUG_SHOW \
		-o $@

# C Versions ________________________________________________________________
# 
lex_iconv_c: 
	@echo "Call to quex"
	@quex -i simple.qx -o $(X) --bet wchar_t --iconv  --language c
	@echo "Compiling"
	gcc -I./ -I$(QUEX_PATH) \
		$(X).c                      \
		-Wall -Werror -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED                         \
		../lexer.c                     \
		-ggdb \
		-DCHARACTER_ENCODING_NAME=\"UTF-8\" \
		-DPRINT_TOKEN_FIRST_NUMBER='402508 - 20' \
		-DPRINT_TOKEN \
	   	-DQUEX_SETTING_BUFFER_SIZE=64 \
		-DQUEX_SETTING_ICONV_TRANSLATION_BUFFER_SIZE=64 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-o $@

lex_icu_c: 
	@echo "Call to quex"
	@quex -i simple.qx -o $(X) --bet wchar_t --icu  --language c
	@echo "Compiling"
	gcc -I./ -I$(QUEX_PATH) \
		$(X).c                      \
		-Wall -Werror -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED                         \
		../lexer.c                     \
		$(LIB_CONV)                   \
		-ggdb                         \
		-DCHARACTER_ENCODING_NAME=\"UTF-8\" \
		-DPRINT_TOKEN_FIRST_NUMBER='402508 - 20' \
		-DPRINT_TOKEN \
	   	-DQUEX_SETTING_BUFFER_SIZE=64 \
		-DQUEX_SETTING_ICONV_TRANSLATION_BUFFER_SIZE=64 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-o $@

lex_codec_c: 
	@echo "Call to quex"
	@quex -i simple.qx -o $(X) --codec utf8  --language C
	@echo "Compiling"
	gcc -I./ -I$(QUEX_PATH) \
		$(X).c                      \
		../lexer.c                     \
		-ggdb \
	   	-DQUEX_SETTING_BUFFER_SIZE=64 \
		-DPRINT_TOKEN \
		-DPRINT_TOKEN_FIRST_NUMBER='402508 - 20' \
		-DCHARACTER_ENCODING_NAME=0x0 \
		-DQUEX_SETTING_ICONV_TRANSLATION_BUFFER_SIZE=64 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-o $@

wiki.txt: wiki.txt.bz2
	bzip2 -dk wiki.txt.bz2

clean:
	rm -rf $(X)-*
	rm -rf $(X).cpp
	rm -rf $(X).c
	rm -rf $(X)
	rm -rf lex_iconv   lex_icu   lex_codec
	rm -rf lex_iconv_c lex_icu_c lex_codec_c
	rm -rf wiki.txt
