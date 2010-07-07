#ifndef __INCLUDE_GUARD__MESSAGING_FRAMEWORK__
#define __INCLUDE_GUARD__MESSAGING_FRAMEWORK__
/* Assume that some low level driver communicates the place where 
 * input is placed via macros. Here, let's use capital letters to
 * express this expectation.                                        */
QUEX_TYPE_CHARACTER*   MESSAGING_FRAMEWORK_BUFFER[DataL];
QUEX_TYPE_CHARACTER    MESSAGING_FRAMEWORK_BUFFER_SIZE = DataL;
#endif // __INCLUDE_GUARD__MESSAGING_FRAMEWORK__
