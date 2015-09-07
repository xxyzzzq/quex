
TEST_FILES = \
		   Buffer_tell_and_seek-1-fb0.exe \
		   Buffer_tell_and_seek-1-fb1.exe \
		   Buffer_tell_and_seek-4-fb0.exe \
		   \
		   Buffer_tell_and_seek-wiostream.exe \
		   \
		   Buffer_move_forward-1-fb0.exe \
		   Buffer_move_forward-1-fb1.exe \
		   Buffer_move_forward-4-fb0.exe \
		   \
		   Buffer_move_backward-1-fb0.exe \
		   Buffer_move_backward-1-fb1.exe \
		   Buffer_move_backward-4-fb0.exe \
		   \
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

HEADERS =  \
		    \
           test-helper.h

DEFS = -DQUEX_OPTION_ASSERTS

CS1 = -DQUEX_TYPE_CHARACTER=uint8_t
CS2 = -DQUEX_TYPE_CHARACTER=uint16_t
CS4 = -DQUEX_TYPE_CHARACTER=uint32_t
FB0 = -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=0 
FB1 = -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=1 
FB5 = -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=5 

CC = g++ -ggdb -Wall -Werror -I$(QUEX_PATH) $(DEFS) -fsanitize=address

all: $(TEST_FILES)

hwut-info:
	@echo $(TEST_FILES)

hwut-end: clean

%-wiostream.exe: %-wiostream.cpp $(HEADERS)
	$(CC) -DQUEX_TYPE_CHARACTER=wchar_t $< -o $@

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

%-error.exe: %-error.cpp $(HEADERS)
	$(CC) $(CS4) $(FB0) $< -o $@

%-1.exe: %.cpp $(HEADERS)
	$(CC) $(CS1) $(FB0) $< -o $@
%-2.exe: %.cpp $(HEADERS)
	$(CC) $(CS2) $(FB0) $< -o $@
%-4.exe: %.cpp $(HEADERS)
	$(CC) $(CS4) $(FB0) $< -o $@

clean: 
	rm -rf $(TEST_FILES)
