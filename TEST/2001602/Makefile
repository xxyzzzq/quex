X = Simple

LIB_CONV  = `icu-config --ldflags --cppflags`

lex_iconv: 
	@echo "Call to quex"
	@quex -i simple.qx -o $(X) -b 2 --iconv --debug-exception
	@echo "Compiling"
	g++ -I./ -I$(QUEX_PATH) \
		$(X).cpp                      \
		-Wall                         \
		../lexer.cpp                     \
		-ggdb \
	   	-DQUEX_SETTING_BUFFER_SIZE=64 \
		-DQUEX_SETTING_ICONV_TRANSLATION_BUFFER_SIZE=64 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-o $@

#-DQUEX_OPTION_DEBUG_SHOW \
#-D__QUEX_OPTION_UNIT_TEST \
#-D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS \
#-D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICONV 

lex_icu: 
	@echo "Call to quex"
	@quex -i simple.qx -o $(X) -b 2 --icu 
	@echo "Compiling"
	g++ -I./ -I$(QUEX_PATH) \
		$(X).cpp                      \
		-Wall                         \
		../lexer.cpp                  \
		$(LIB_CONV)                   \
		-ggdb                         \
	   	-DQUEX_SETTING_BUFFER_SIZE=64 \
		-DQUEX_SETTING_ICONV_TRANSLATION_BUFFER_SIZE=64 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED  \
		-o $@

lex_codec: 
	@echo "Call to quex"
	@quex -i simple.qx -o $(X) --codec utf8 --debug-exception
	@echo "Compiling"
	g++ -I./ -I$(QUEX_PATH)              \
		$(X).cpp                         \
		-Wall                            \
		../lexer.cpp                     \
		-ggdb                            \
	   	-DQUEX_SETTING_BUFFER_SIZE=64    \
		-DQUEX_SETTING_ICONV_TRANSLATION_BUFFER_SIZE=64 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED  \
		-o $@
#-DQUEX_OPTION_DEBUG_SHOW 

clean:
	rm -rf $(X)-*
	rm -rf $(X).cpp
	rm -rf $(X)
	rm -rf a.out
	rm -rf lex_icu lex_iconv lex_codec
