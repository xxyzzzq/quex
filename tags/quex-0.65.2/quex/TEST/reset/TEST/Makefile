include $(QUEX_PATH)/quex/code_base/core.mkd

FILES = lexer codec-lexer iconv-lexer icu-lexer lexer-x

CC = g++ -I$(QUEX_PATH) \
	 -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
	 -ggdb

codec-lexer: lexer.cpp 
	quex -i simple-hindi.qx -o Simple --token-policy single --codec utf8 --debug-exception
	$(CC) lexer.cpp Simple.cpp  -o $@ \
		  -DQUEX_SETTING_BUFFER_SIZE=33                     \
	      -D__QUEX_SETTING_TEST_UTF8 

iconv-lexer: lexer.cpp 
	quex -i simple-hindi.qx -o Simple --token-policy single --iconv --bet wchar_t --debug-exception
	$(CC) lexer.cpp Simple.cpp  -o $@ \
		  -DQUEX_SETTING_BUFFER_SIZE=20                     \
		  -DQUEX_SETTING_TRANSLATION_BUFFER_SIZE=20          \
		  -D__QUEX_SETTING_TEST_UTF8           

icu-lexer: lexer.cpp 
	quex -i simple-hindi.qx -o Simple --token-policy single --icu --bet wchar_t --debug-exception
	$(CC) lexer.cpp Simple.cpp  -o $@ \
		  `icu-config --ldflags`                            \
		  -DQUEX_SETTING_BUFFER_SIZE=20                     \
		  -DQUEX_SETTING_TRANSLATION_BUFFER_SIZE=20         \
		  -D__QUEX_SETTING_TEST_UTF8           

lexer: lexer.cpp 
	quex -i simple.qx -o Simple --token-policy single --debug-exception
	$(CC) lexer.cpp Simple.cpp  -o $@ \
		 -DQUEX_SETTING_BUFFER_SIZE=14                 \
		 -DQUEX_SETTING_TRANSLATION_BUFFER_SIZE=9           
		 #-DQUEX_OPTION_DEBUG_SHOW                      \

lexer-x: lexer-x.cpp
	quex -i simple.qx -o Simple --token-policy single --debug-exception
	$(CC) lexer-x.cpp Simple.cpp  -o $@ \
		 -DQUEX_SETTING_BUFFER_SIZE=14                      \
		 -DQUEX_SETTING_TRANSLATION_BUFFER_SIZE=9           

hwut-begin: clean

hwut-info:
	@echo $(FILES)

clean:
	rm -f Simple*
	rm -f $(FILES)
