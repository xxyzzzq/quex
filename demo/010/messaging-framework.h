#ifndef __INCLUDE_GUARD__MESSAGING_FRAMEWORK__
#define __INCLUDE_GUARD__MESSAGING_FRAMEWORK__

/* Assume that some low level driver communicates the place where 
 * input is placed via macros.                                     */
#define  MESSAGING_FRAMEWORK_BUFFER_SIZE  ((size_t)(65536))
extern QUEX_TYPE_CHARACTER   MESSAGING_FRAMEWORK_BUFFER[MESSAGING_FRAMEWORK_BUFFER_SIZE];

extern size_t messaging_framework_receive(QUEX_TYPE_CHARACTER** buffer);
extern size_t messaging_framework_receive_syntax_chunk(QUEX_TYPE_CHARACTER** buffer);
extern size_t messaging_framework_receive_into_buffer(QUEX_TYPE_CHARACTER*, size_t);
extern size_t messaging_framework_receive_to_internal_buffer();
extern void   messaging_framework_release(uint8_t*);

#endif // __INCLUDE_GUARD__MESSAGING_FRAMEWORK__
