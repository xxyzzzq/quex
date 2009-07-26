X = Simple
LIB_CONV  = `icu-config --ldflags`

lex_iconv: 
	@echo "Call to quex"
	@quex -i simple.qx -o $(X) -b wchar_t --iconv  --token-prefix TKN_
	@echo "Compiling"
	g++ -I./ -I$(QUEX_PATH) \
		$(X)-core-engine.cpp          \
		$(X).cpp                      \
		-Wall                         \
		lexer.cpp                     \
		-ggdb \
	   	-DQUEX_SETTING_BUFFER_SIZE=64 \
		-DQUEX_SETTING_ICONV_TRANSLATION_BUFFER_SIZE=64 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-o $@

lex_icu: 
	@echo "Call to quex"
	@quex -i simple.qx -o $(X) -b wchar_t --icu  --token-prefix TKN_
	@echo "Compiling"
	g++ -I./ -I$(QUEX_PATH) \
		$(LIB_CONV) \
		$(X)-core-engine.cpp          \
		$(X).cpp                      \
		-Wall                         \
		lexer.cpp                     \
		-ggdb \
	   	-DQUEX_SETTING_BUFFER_SIZE=64 \
		-DQUEX_SETTING_ICONV_TRANSLATION_BUFFER_SIZE=64 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-o $@

lex_codec: 
	@echo "Call to quex"
	@quex -i simple.qx -o $(X) --codec utf8  --token-prefix TKN_
	@echo "Compiling"
	g++ -I./ -I$(QUEX_PATH) \
		$(X)-core-engine.cpp          \
		$(X).cpp                      \
		lexer.cpp                     \
		-ggdb \
	   	-DQUEX_SETTING_BUFFER_SIZE=64 \
		-DQUEX_SETTING_ICONV_TRANSLATION_BUFFER_SIZE=64 \
		-DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		-o $@

wiki.txt: wiki.txt.bz2
	cp       wiki.txt.bz2 backup.tmp
	bzip2 -d wiki.txt.bz2
	mv       backup.tmp wiki.txt.bz2

clean:
	rm -rf $(X)-core-engine.cpp
	rm -rf $(X)-token_ids
	rm -rf $(X).cpp
	rm -rf $(X)
	rm -rf lex_iconv lex_icu lex_codec
	rm -rf wiki.txt
