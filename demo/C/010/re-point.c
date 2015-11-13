#include<stdio.h>    
#include<string.h> 

#include "tiny_lexer.h"
#include "messaging-framework.h"

void test(quex_tiny_lexer* qlex, QUEX_TYPE_CHARACTER* memory);

QUEX_TYPE_CHARACTER memory_a[MESSAGING_FRAMEWORK_BUFFER_SIZE+2];
QUEX_TYPE_CHARACTER memory_b[MESSAGING_FRAMEWORK_BUFFER_SIZE+2];
QUEX_TYPE_CHARACTER memory_c[MESSAGING_FRAMEWORK_BUFFER_SIZE+2];

int 
main(int argc, char** argv) 
{        
    quex_tiny_lexer      qlex;
    QUEX_TYPE_CHARACTER* remainder = 0x0;

    /* Fill at position 'memory + 1'. 'memory + 0' holds buffer limit code.  */
    receiver_copy_here(&memory_a[1], MESSAGING_FRAMEWORK_BUFFER);

    quex_tiny_lexer_from_memory(&qlex, 
                                &memory_a[0], 
                                &memory_a[MESSAGING_FRAMEWORK_BUFFER_SIZE+2], 
                                &memory_a[MESSAGING_FRAMEWORK_BUFFER_SIZE+2]);

    /* In this example we do the same as in 'point.cpp'
     * -- only that the use different buffers for each run.
     *    This requires a 'reset_memory' call, as shown below. */
    test(&qlex, NULL);
    test(&qlex, memory_b);
    test(&qlex, memory_c);

    /* Delete remaining memory buffer that is still inside the analyzer */
    remainder = QUEX_NAME(reset_memory)(&qlex, 0x0, 0, 0x0);
    if( remainder != 0x0 ) free(remainder);

    QUEX_NAME(destruct)(&qlex);
    return 0;
}

void 
void test(quex_tiny_lexer* qlex, QUEX_TYPE_CHARACTER* memory);
{
    QUEX_TYPE_TOKEN       token;           
    QUEX_TYPE_CHARACTER*  buffer      = 0x0;
    size_t                buffer_size = 0;
    size_t                UTF8BufferSize = 1024;
    char                  utf8_buffer[1024];
    QUEX_TYPE_CHARACTER*  prev_memory = 0x0;

    if( memory ) {
        /* Fill at position 'memory + 1'. 'memory + 0' holds buffer limit 
         * code.                                                             */
        receiver_copy_here(&memory[1], MESSAGING_FRAMEWORK_BUFFER);

        quex_tiny_lexer_reset_memory(&qlex, 
                                     &memory[0], 
                                     &memory[MESSAGING_FRAMEWORK_BUFFER_SIZE+2], 
                                     &memory[MESSAGING_FRAMEWORK_BUFFER_SIZE+2]);
    }

    /* Loop until the 'termination' token arrives                            */
    QUEX_NAME(token_p_swap)(qlex, &token);
    do {
        QUEX_NAME(receive)(qlex);

        if( token._id != QUEX_TKN_TERMINATION )
            printf("Consider: %s \n", QUEX_NAME_TOKEN(get_string)(&token, utf8_buffer, UTF8BufferSize));

        if( token._id == QUEX_TKN_BYE ) 
            printf("##\n");
        
    } while( token._id != QUEX_TKN_TERMINATION );

    QUEX_NAME_TOKEN(destruct)(&token);

    printf("<<End of Run>>\n");
}

