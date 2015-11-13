#include<stdio.h>    
#include<string.h> 

#include "lexPlain.h"
#include "messaging_framework.h"

static void  test(QUEX_TYPE_ANALYZER* qlex, QUEX_TYPE_CHARACTER* memory);
static void  print_token(quex_Token*  token);

QUEX_TYPE_CHARACTER   memory_a[MESSAGING_FRAMEWORK_BUFFER_SIZE+2];
QUEX_TYPE_CHARACTER   memory_b[MESSAGING_FRAMEWORK_BUFFER_SIZE+2];
QUEX_TYPE_CHARACTER   memory_c[MESSAGING_FRAMEWORK_BUFFER_SIZE+2];

int 
main(int argc, char** argv) 
/* In this example, the lexical analyzer's buffer is given from an external
 * source. The first memory chunk 'memory_a' is passed upon construction of the
 * lexical analyzer. The next two runs with 'memory_b' and 'memory'b' are
 * initiated by passing the memory with the 'reset' function.                */
{        
    quex_lexPlain        qlex; 

    /* Fill at position 'memory + 1'. 'memory + 0' holds buffer limit code.  */
    receiver_copy_here(&memory_a[1], MESSAGING_FRAMEWORK_BUFFER_SIZE);

    quex_lexPlain_from_memory(&qlex, 
                              &memory_a[0], 
                              MESSAGING_FRAMEWORK_BUFFER_SIZE+2, 
                              &memory_a[MESSAGING_FRAMEWORK_BUFFER_SIZE+2]);

    test(&qlex, NULL);            /* treat memory given during construction. */
    test(&qlex, memory_b);        /* pass 'memory_b' upon reset, then run.   */
    test(&qlex, memory_c);        /* pass 'memory_c' upon reset, then run.   */

    QUEX_NAME(destruct)(&qlex);
    return 0;
}

static void 
test(quex_lexPlain* qlex, QUEX_TYPE_CHARACTER* memory)
{
    QUEX_TYPE_TOKEN       token;           

    if( memory ) {
        /* Fill at position 'memory + 1'. 'memory + 0' holds buffer limit 
         * code.                                                             */
        receiver_copy_here(&memory[1], MESSAGING_FRAMEWORK_BUFFER_SIZE);

        quex_lexPlain_reset_memory(qlex, 
                                   &memory[0], 
                                   MESSAGING_FRAMEWORK_BUFFER_SIZE+2, 
                                   &memory[MESSAGING_FRAMEWORK_BUFFER_SIZE+2]);
    }

    /* Loop until the 'termination' token arrives                            */
    QUEX_NAME(token_p_swap)(qlex, &token);
    do {
        QUEX_NAME(receive)(qlex);

        print_token(&token);
        
    } while( token._id != QUEX_TKN_TERMINATION );

    QUEX_NAME_TOKEN(destruct)(&token);

    printf("<terminated>\n");
}

static void
print_token(quex_Token*  token)
{
    size_t PrintBufferSize = 1024;
    char   print_buffer[1024];

    printf("   Token: %s\n", QUEX_NAME_TOKEN(get_string)(token, print_buffer, 
                                                         PrintBufferSize));
}
