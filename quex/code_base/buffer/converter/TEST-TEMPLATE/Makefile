TEST_TEMPLATE_RESULTS := \
				  Buffer_tell_and_seek.cpp   \
		          Buffer_seek_forward.cpp    \
		          Buffer_seek_backward.cpp   \
				  converter.cpp              \
				  converter-statefulness.cpp \
				  one-beat.cpp               \
				  n-beat.cpp                 \
		          seek_character_index.cpp   \
		          seek_character_index-zikzak.cpp 

%.cpp: $(TEST_TEMPLATE_DIR)/%-template.cpp
	sed   -e 's/\_\_\_NEW\_\_\_/$(NEW_OPERATOR)/g' $<         \
	| sed -e 's/\_\_\_CONVERT\_\_\_/$(CONVERTER)/g'           \
	| sed -e 's/\_\_\_FILLER_TYPE\_\_\_/$(FILLER_TYPE)/g'     \
	| sed -e 's/\_\_\_UCS_4_BYTE_BE\_\_\_/$(UCS_4_BYTE_BE)/g' \
	| sed -e 's/\_\_\_UCS_4_BYTE_LE\_\_\_/$(UCS_4_BYTE_LE)/g' \
	| sed -e 's/\_\_\_UCS_2_BYTE_LE\_\_\_/$(UCS_2_BYTE_LE)/g' \
	| sed -e 's/\_\_\_UCS_UTF8\_\_\_/$(UCS_UTF8)/g'           \
	| sed -e 's/\_\_\_DATA_DIR\_\_\_/$(subst /,\/,$(TEST_TEMPLATE_DIR))/g'  \
	> $@

