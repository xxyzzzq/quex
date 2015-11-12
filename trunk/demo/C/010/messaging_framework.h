#ifndef __INCLUDE_GUARD__MESSAGING_FRAMEWORK__
#define __INCLUDE_GUARD__MESSAGING_FRAMEWORK__

#ifdef QUEX_EXAMPLE_WITH_CONVERTER 
#   define ELEMENT_TYPE uint8_t
#   include "tiny_lexer_utf8.h"
#else
#   define ELEMENT_TYPE QUEX_TYPE_CHARACTER
#   include "tiny_lexer.h"
#endif

typedef struct {
    ELEMENT_TYPE* begin_p;
    ELEMENT_TYPE* end_p;
} MemoryChunk;

/* Assume that some low level driver communicates the place where 
 * input is placed via macros.                                     */
#define  MESSAGING_FRAMEWORK_BUFFER_SIZE  ((size_t)(512))
extern ELEMENT_TYPE   MESSAGING_FRAMEWORK_BUFFER[MESSAGING_FRAMEWORK_BUFFER_SIZE];

extern size_t receiver_fill(ELEMENT_TYPE** buffer);
extern size_t receiver_fill_syntax_chunk(ELEMENT_TYPE** buffer);
extern size_t receiver_fill_whole_characters(ELEMENT_TYPE** rx_buffer);
extern size_t receiver_fill_to_internal_buffer();
extern size_t receiver_copy(ELEMENT_TYPE*, size_t);
extern size_t receiver_copy_syntax_chunk(ELEMENT_TYPE* BufferBegin, 
                                         size_t        BufferSize);

#endif /*_INCLUDE_GUARD__MESSAGING_FRAMEWORK_*/
