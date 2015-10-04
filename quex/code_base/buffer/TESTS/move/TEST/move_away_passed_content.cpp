/* PURPOSE: Test Buffer_move_away_passed_content()
 *
 * The tested function shall free some space ahead inside the buffer,
 * so that new content can be loaded. Detailed comment, see function
 * definition.
 *
 * Moving depends on:   * _read_p, 
 *                      * _lexeme_start_p
 *                      * whether the buffer contains the end of file or not.
 *                      * QUEX_SETTING_BUFFER_MIN_FALLBACK_N
 *                      * QUEX_TYPE_CHARACTER
 *
 * The last two are compile-time parameters. The first three may be
 * varried dynamically. 
 *
 * EXPERIMENT: Setup buffer of 5 elements.
 *
 * Let this file be compiled with '-DQUEX_SETTING_BUFFER_MIN_FALLBACK_N=3'
 * for all experiments. Multiple versions of compiled objects may exist:
 *
 *        QUEX_TYPE_CHARACTER  QUEX_SETTING_BUFFER_MIN_FALLBACK_N
 *          uint8_t             0
 *          uint8_t             1
 *          uint8_t             2
 *          uint32_t            2
 *
 * The parameters '_read_p' and '_lexeme_start_p' are varried the following
 * way:
 *    _lexeme_start_p -> begin ... end of buffer
 *    _read_p         -> begin, 
 *                       _lexeme_start_p-1, _lexeme_start_p, _lexeme_start_p+1, 
 *                       end of buffer
 *    end of file     = true, false
 *
 * Before each copying process the buffer is reset into its initial state. Test
 * cases are generated by hwuts generator, i.e. 'hwut gen this-file.c'.      */

/* 
<<hwut-iterator: Gen>> 
------------------------------------------------------------------------
#include <stdint.h>
------------------------------------------------------------------------
    int lexeme_start_i;    int read_i;                                   int eof_f; 
    |0:4|;                 |lexeme_start_i-1:lexeme_start_i+1| in |0:4|; [0, 1];

------------------------------------------------------------------------
*/
#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/buffer/filler/BufferFiller.i>
#include <quex/code_base/buffer/Buffer_debug.i>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/converter_helper/from-unicode-buffer.i>
#include <quex/code_base/single.i>
#include <cstring>
#include <hwut_unit.h>

#include <move_away_passed_content-gen.h>
using namespace    quex;
static void self_init(QUEX_NAME(Buffer)* buffer, Gen_t* it);
static void self_print(QUEX_NAME(Buffer)* buffer);
static void self_prepare_memory(QUEX_NAME(Buffer)*   buffer, 
                                QUEX_TYPE_CHARACTER* end_p);


static int cl_has(int argc, char** argv, const char* What)
{ return argc > 1 && strcmp(argv[1], What) == 0; }

int
main(int argc, char** argv)
{
    QUEX_NAME(Buffer)  buffer;
    Gen_t              it;
    QUEX_TYPE_CHARACTER lsp_char, rp_char;

    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("move_away_passed_content: (BPC=%i, FB=%i);\n", 
               sizeof(QUEX_TYPE_CHARACTER),
               (int)QUEX_SETTING_BUFFER_MIN_FALLBACK_N);
        return 0;
    }
    stderr = stdout;

    Gen_init(&it);
    
    printf("        lexeme_start_p: read_p: end_p: end_index: buffer:\n");
    while( Gen_next(&it) ) {
        self_init(&buffer, &it);
        printf("\n-( %2i )---------------------------------------------\n", (int)Gen_key_get(&it));
        self_print(&buffer);

        lsp_char = *buffer._lexeme_start_p;
        rp_char  = *buffer._read_p;

        QUEX_NAME(Buffer_move_away_passed_content)(&buffer);

        self_print(&buffer);

        /* Asserts after print, so that errors appear clearly. */
        hwut_verify(   buffer._read_p         <= &buffer._memory._front[1 + QUEX_SETTING_BUFFER_MIN_FALLBACK_N] 
                    || buffer._lexeme_start_p <= &buffer._memory._front[1 + QUEX_SETTING_BUFFER_MIN_FALLBACK_N]);
        hwut_verify(lsp_char == *buffer._lexeme_start_p);
        hwut_verify(rp_char  == *buffer._read_p);

        QUEX_NAME(Buffer_destruct)(&buffer);
    }
}

static QUEX_TYPE_CHARACTER  content[] = { '5', '4', '3', '2', '1' }; 
ptrdiff_t                   content_size = sizeof(content)/sizeof(content[0]);
static QUEX_TYPE_CHARACTER  memory[12];
ptrdiff_t                   MemorySize = 12;

static void
self_init(QUEX_NAME(Buffer)* buffer, Gen_t* it)
{
    QUEX_TYPE_CHARACTER*   end_p;
    ptrdiff_t              memory_size = MemorySize;

    if( it->eof_f ) {
        end_p       = &memory[content_size+1];
        *end_p      = QUEX_SETTING_BUFFER_LIMIT_CODE;
    }
    else {
        end_p       = (QUEX_TYPE_CHARACTER*)0;
        memory_size = content_size + 2;
    }

    /* Filler = 0x0, otherwise, buffer would start loading content */
    QUEX_NAME(Buffer_construct)(buffer, 
                                (QUEX_NAME(BufferFiller)*)0x0, 
                                &memory[0], memory_size, end_p, 
                                E_Ownership_EXTERNAL);

    self_prepare_memory(buffer, end_p);

    buffer->_lexeme_start_p = &buffer->_memory._front[it->lexeme_start_i+1];
    buffer->_read_p         = &buffer->_memory._front[it->read_i+1];
}

static void
self_prepare_memory(QUEX_NAME(Buffer)* buffer, QUEX_TYPE_CHARACTER* end_p)
{
    static QUEX_TYPE_CHARACTER  content[] = { '5', '4', '3', '2', '1' }; 
    ptrdiff_t                   content_size = sizeof(content)/sizeof(content[0]);

    memset(&buffer->_memory._front[1], (QUEX_TYPE_CHARACTER) - 1, 
           (buffer->_memory._back - buffer->_memory._front -1)*sizeof(QUEX_TYPE_CHARACTER));
    memcpy(&buffer->_memory._front[1], (void*)content, 
           sizeof(content));
    if( end_p ) *end_p = QUEX_SETTING_BUFFER_LIMIT_CODE;
    QUEX_BUFFER_ASSERT_limit_codes_in_place(buffer);

    QUEX_NAME(Buffer_input_end_set)(buffer, end_p, content_size);
}

static void
self_print(QUEX_NAME(Buffer)* buffer)
{
    /**/
    printf("        @%i '%c';         @%i '%c'; @%2i;   @%i;       ", 
           (int)(buffer->_lexeme_start_p - buffer->_memory._front),
           (int)(*(buffer->_lexeme_start_p)),
           (int)(buffer->_read_p - buffer->_memory._front),
           (int)(*(buffer->_read_p)),
           (int)(buffer->input.end_p ? buffer->input.end_p - buffer->_memory._front : -1),
           (int)buffer->input.end_character_index);
    /**/
    QUEX_NAME(Buffer_show_content_intern)(buffer);
    printf("\n");
}
