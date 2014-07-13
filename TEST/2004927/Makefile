X = Simple
LIB_CONV  = `icu-config --ldflags --cppflags`

lex_iconv: 
	@echo "Call to quex"
	@quex -i simple.qx -o $(X) --bet wchar_t --iconv --debug-exception
	@echo "Compiling"
	g++ -I./ -I$(QUEX_PATH) \
		$(X).cpp                      \
		-Wall -Werror -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED                         \
		../lexer.cpp                     \
		-ggdb \
	   	-DQUEX_SETTING_BUFFER_SIZE=64 \
		-DQUEX_SETTING_ICONV_TRANSLATION_BUFFER_SIZE=64 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-o $@

lex_icu: 
	@echo "Call to quex"
	@quex -i simple.qx -o $(X) --bet wchar_t --icu  
	@echo "Compiling"
	g++ -I./ -I$(QUEX_PATH)           \
		$(X).cpp                      \
		-Wall -Werror -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED                         \
		../lexer.cpp                  \
		$(LIB_CONV)                   \
		-ggdb                         \
	   	-DQUEX_SETTING_BUFFER_SIZE=64 \
		-DQUEX_SETTING_ICONV_TRANSLATION_BUFFER_SIZE=64 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-o $@

lex_codec: 
	@echo "Call to quex"
	@quex -i simple.qx -o $(X) --codec utf8  
	@echo "Compiling"
	g++ -I./ -I$(QUEX_PATH) \
		$(X).cpp                      \
		-Wall -Werror -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED                         \
		../lexer.cpp                     \
		-ggdb \
	   	-DQUEX_SETTING_BUFFER_SIZE=64 \
		-DQUEX_SETTING_ICONV_TRANSLATION_BUFFER_SIZE=64 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-o $@


clean:
	rm -rf $(X)-*
	rm -rf $(X).cpp
	rm -rf $(X)
	rm -rf a.out
	rm -rf lex_iconv lex_icu lex_codec
