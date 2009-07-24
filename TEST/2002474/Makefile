X = Simple

all: $(X).cpp 
	@echo "Compiling"
	@g++ -I./ -I$(QUEX_PATH) \
		$(X)-core-engine.cpp          \
		$(X).cpp                      \
		lexer.cpp                     \
		-ggdb \
		-DQUEX_OPTION_TOKEN_SENDING_VIA_QUEUE \
		-DQUEX_SETTING_BUFFER_SIZE=65536 
	   	#-D__QUEX_OPTION_DEBUG_STATE_TRANSITION_REPORTS \
		#-lefence
		# -D__QUEX_OPTION_UNIT_TEST_INPUT_STRATEGY_ICONV 

wiki.txt: wiki.txt.bz2
	cp       wiki.txt.bz2 backup.tmp
	bzip2 -d wiki.txt.bz2
	cp       backup.tmp wiki.txt.bz2

$(X).cpp: simple.qx
	@echo "Call to quex"
	@python $(QUEX_PATH)/quex-exe.py -i $< -o $(X) -b wchar_t --iconv --token-prefix  TKN_ 


clean:
	rm -rf $(X)-core-engine.cpp
	rm -rf $(X)-token_ids
	rm -rf $(X).cpp
	rm -rf $(X)
	rm -rf a.out
	rm -rf wiki.txt
