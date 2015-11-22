#ifndef INCLUDE_GUARD_TEST_MOVE_AWAY_PASSED_CONTENT_COMMON_H
#define INCLUDE_GUARD_TEST_MOVE_AWAY_PASSED_CONTENT_COMMON_H

#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/buffer/filler/BufferFiller.i>
#include <quex/code_base/buffer/Buffer_debug.i>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/converter_helper/from-unicode-buffer.i>
#include <quex/code_base/single.i>
#include <cstring>
#include <hwut_unit.h>

/* Define static functions included in each test file:
 * => avoid dedicated compilation for each setup.
 * => avoid mentioning the 'common.cpp' on each compiler command line.       */
using namespace quex; /* One should not do this in a header ...              */


static void self_print(QUEX_NAME(Buffer)* buffer);
static void memory_fill_with_content(QUEX_TYPE_CHARACTER* memory, size_t MemorySize, 
                                     QUEX_TYPE_CHARACTER* content, size_t ContentSize);
static int  cl_has(int argc, char** argv, const char* What);
static void instantiate_iterator(QUEX_NAME(Buffer)* buffer, G_t* it,
                                 QUEX_TYPE_CHARACTER* memory, ptrdiff_t MemorySize,
                                 QUEX_TYPE_CHARACTER* content, ptrdiff_t ContentSize);


static int cl_has(int argc, char** argv, const char* What)
{ return argc > 1 && strcmp(argv[1], What) == 0; }

static void
memory_fill_with_content(QUEX_TYPE_CHARACTER* memory, size_t MemorySize, 
                         QUEX_TYPE_CHARACTER* content, size_t ContentSize)
{
    memset((void*)&memory[1], 0xFF, 
           (MemorySize - 2)*sizeof(QUEX_TYPE_CHARACTER));
    memcpy((void*)&memory[1], (void*)content, 
           ContentSize*sizeof(QUEX_TYPE_CHARACTER)); 
}

static void
self_print(QUEX_NAME(Buffer)* buffer)
{
    printf("        @%i '%c';         @%i '%c'; @%2i;   @%i;       ", 
           (int)(buffer->_lexeme_start_p - buffer->_memory._front),
           (int)(*(buffer->_lexeme_start_p)),
           (int)(buffer->_read_p - buffer->_memory._front),
           (int)(*(buffer->_read_p)),
           (int)(buffer->input.character_index_end_of_stream != -1 ? buffer->input.end_p - buffer->_memory._front : -1),
           (int)QUEX_NAME(Buffer_input_character_index_end)(buffer));

    QUEX_NAME(Buffer_show_content_intern)(buffer);
    printf("\n");
}

static void
instantiate_iterator(QUEX_NAME(Buffer)* buffer, G_t* it,
                     QUEX_TYPE_CHARACTER* memory, ptrdiff_t MemorySize,
                     QUEX_TYPE_CHARACTER* content, ptrdiff_t ContentSize)
/* Sets the buffer up according to what is specified in the iterator:
 *
 *  it.eof_f          --> size of memory = size of content or whole memory.
 *                        set the 'end of file' notifier.
 *  it.read_i         --> position of the buffer's _read_p.
 *  it.lexeme_start_i --> position of the buffer's _lexeme_start_p.
 *                                                                           */
{
    QUEX_TYPE_CHARACTER*   BeginP;
    QUEX_TYPE_CHARACTER*   end_p;
    ptrdiff_t              memory_size = it->eof_f ? MemorySize : ContentSize + 2;

    end_p  = &memory[ContentSize + 1];
    *end_p = QUEX_SETTING_BUFFER_LIMIT_CODE;

    /* Filler = 0x0, otherwise, buffer would start loading content */
    assert(memory_size <= MemorySize);
    assert(end_p - &memory[1] < memory_size);
    QUEX_NAME(Buffer_construct)(buffer, 
                                (QUEX_NAME(BufferFiller)*)0x0, 
                                &memory[0], memory_size, end_p, 
                                E_Ownership_EXTERNAL);

    memory_fill_with_content(&memory[0], MemorySize, 
                             &content[0], ContentSize);

    BeginP                  = &buffer->_memory._front[1];
    buffer->_lexeme_start_p = &BeginP[it->lexeme_start_i];
    buffer->_read_p         = &BeginP[it->read_i];

    QUEX_NAME(Buffer_register_content)(buffer, end_p, 0);
    if( it->eof_f ) {
        QUEX_NAME(Buffer_register_eos)(buffer, end_p - BeginP); 
    }

    QUEX_BUFFER_ASSERT_limit_codes_in_place(buffer);
}
#endif /* INCLUDE_GUARD_TEST_MOVE_AWAY_PASSED_CONTENT_COMMON_H */

