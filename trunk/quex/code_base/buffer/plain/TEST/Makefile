TEST_FILES = \
	       BufferFiller_forward_load-1-fb0.exe \
	       BufferFiller_forward_load-2-fb0.exe \
	       BufferFiller_forward_load-4-fb0.exe \
		   \
	       BufferFiller_forward_load-1-fb1.exe \
	       BufferFiller_forward_load-2-fb1.exe \
	       BufferFiller_forward_load-4-fb1.exe \
		   \
	       BufferFiller_forward_load-1-fb5.exe \
	       BufferFiller_forward_load-2-fb5.exe \
	       BufferFiller_forward_load-4-fb5.exe \
		   \
	       BufferFiller_forward_load-error.exe \
		   \
	       BufferFiller_backward_load-1.exe \
	       BufferFiller_backward_load-2.exe \
	       BufferFiller_backward_load-4.exe \
	       #BufferFiller_backward_load.exe

HEADERS =  $(QUEX_PATH)/quex/code_base/definitions \
           $(QUEX_PATH)/quex/code_base/asserts \
           $(QUEX_PATH)/quex/code_base/compatibility/inttypes.h \
           $(QUEX_PATH)/quex/code_base/compatibility/pseudo-stdbool.h \
           $(QUEX_PATH)/quex/code_base/buffer/Buffer.i \
           $(QUEX_PATH)/quex/code_base/buffer/Buffer \
           $(QUEX_PATH)/quex/code_base/buffer/Buffer_debug.i \
           $(QUEX_PATH)/quex/code_base/buffer/BufferFiller \
           $(QUEX_PATH)/quex/code_base/temporary_macros_on \
           $(QUEX_PATH)/quex/code_base/temporary_macros_off \
           $(QUEX_PATH)/quex/code_base/buffer/BufferFiller.i \
           $(QUEX_PATH)/quex/code_base/buffer/plain/BufferFiller_Plain \
           $(QUEX_PATH)/quex/code_base/buffer/InputPolicy \
           test-helper.h

DEFS = -DQUEX_OPTION_ASSERTS

CS1 = -DQUEX_CHARACTER_TYPE=uint8_t
CS2 = -DQUEX_CHARACTER_TYPE=uint16_t
CS4 = -DQUEX_CHARACTER_TYPE=uint32_t
FB0 = -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 
FB1 = -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=1 
FB5 = -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=5 

CC = g++ -ggdb -I$(QUEX_PATH) $(DEFS) 

all: $(TEST_FILES)

hwut-info:
	@echo $(TEST_FILES)

%-4-fb0.exe: %.cpp $(HEADERS)
	$(CC) $(CS4) $(FB0) $< -o $@
%-4-fb1.exe: %.cpp $(HEADERS)
	$(CC) $(CS4) $(FB1) $< -o $@
%-4-fb5.exe: %.cpp $(HEADERS)
	$(CC) $(CS4) $(FB5) $< -o $@

%-2-fb0.exe: %.cpp $(HEADERS)
	$(CC) $(CS2) $(FB0) $< -o $@
%-2-fb1.exe: %.cpp $(HEADERS)
	$(CC) $(CS2) $(FB1) $< -o $@
%-2-fb5.exe: %.cpp $(HEADERS)
	$(CC) $(CS2) $(FB5) $< -o $@

%-1-fb0.exe: %.cpp $(HEADERS)
	$(CC) $(CS1) $(FB0) $< -o $@
%-1-fb1.exe: %.cpp $(HEADERS)
	$(CC) $(CS1) $(FB1) $< -o $@
%-1-fb5.exe: %.cpp $(HEADERS)
	$(CC) $(CS1) $(FB5) $< -o $@

%-error.exe: %-error.cpp
	$(CC) $(CS4) $(FB0) $< -o $@

%-1.exe: %.cpp $(HEADERS)
	$(CC) $(CS1) $(FB0) $< -o $@
%-2.exe: %.cpp $(HEADERS)
	$(CC) $(CS2) $(FB0) $< -o $@
%-4.exe: %.cpp $(HEADERS)
	$(CC) $(CS4) $(FB0) $< -o $@

clean: 
	rm -rf $(TEST_FILES)
