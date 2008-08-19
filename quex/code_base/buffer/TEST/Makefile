TEST_FILES = \
	       BufferFiller_forward_copy.exe \
	       BufferFiller_backward_copy.exe \
	       BufferFiller_forward_copy-32.exe \
	       BufferFiller_backward_copy-32.exe

DEFS = \
	   -DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=5 \
	   \
	   -D__QUEX_OPTION_UNIT_TEST_QUEX_BUFFER_LOADS \
	   -DQUEX_OPTION_ASSERTS

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
           $(QUEX_PATH)/quex/code_base/buffer/plain/BufferFiller_Plain.i \
           $(QUEX_PATH)/quex/code_base/buffer/InputPolicy \
           test-helper.h

all: $(TEST_FILES)

hwut-info:
	@echo $(TEST_FILES)

%.exe: %.cpp
	g++ -DQUEX_CHARACTER_TYPE=uint8_t \
		-ggdb -I$(QUEX_PATH) $(DEFS) $< -o $@

%-32.exe: %.cpp
	g++ -DQUEX_CHARACTER_TYPE=uint32_t \
		-ggdb -I$(QUEX_PATH) $(DEFS) $< -o $@

clean: 
	rm -rf $(TEST_FILES)
