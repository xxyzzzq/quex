#include<stdio.h>    
#include<string.h> 

#include "lexPlain"
#include "receiver.h"

static void  test(quex::lexPlain* qlex, QUEX_TYPE_LEXATOM* memory);

/* Memory size = much bigger than required to hold the complete content.     */
#define  MEMORY_SIZE  (MESSAGING_FRAMEWORK_BUFFER_SIZE*2)

QUEX_TYPE_LEXATOM   memory_a[MEMORY_SIZE];
QUEX_TYPE_LEXATOM   memory_b[MEMORY_SIZE];
QUEX_TYPE_LEXATOM   memory_c[MEMORY_SIZE];

int 
main(int argc, char** argv) 
/* In this example, the lexical analyzer's buffer is given from an external
 * source. The first memory chunk 'memory_a' is passed upon construction of the
 * lexical analyzer. The next two runs with 'memory_b' and 'memory'b' are
 * initiated by passing the memory with the 'reset' function.                */
{        
    quex::lexPlain*  qlex; 
    size_t           received_n;

    /* Fill at 'memory + 1'; 'memory + 0' holds buffer limit code.           */
    received_n = receiver_copy_here(&memory_a[1], MEMORY_SIZE-1);
    __quex_assert(received_n < MEMORY_SIZE-2);

    qlex = new quex::lexPlain(&memory_a[0], MEMORY_SIZE, &memory_a[received_n+1]);

    test(qlex, NULL);            /* treat memory given during construction. */
    test(qlex, memory_b);        /* pass 'memory_b' upon reset, then run.   */
    test(qlex, memory_c);        /* pass 'memory_c' upon reset, then run.   */

    delete qlex;

    return 0;
}

static void 
test(quex::lexPlain* qlex, QUEX_TYPE_LEXATOM* memory)
{
    QUEX_TYPE_TOKEN       token;           
    size_t                received_n;

    if( memory ) {
        /* Fill at 'memory + 1'; 'memory + 0' holds buffer limit code.       */
        received_n = receiver_copy_here(&memory[1], MEMORY_SIZE-1);
        __quex_assert(received_n < MEMORY_SIZE-2);

        qlex->reset(&memory[0], MEMORY_SIZE, &memory[received_n+1]);
    }

    /* Loop until the 'termination' token arrives                            */
    QUEX_NAME(token_p_swap)(qlex, &token);
    do {
        QUEX_NAME(receive)(qlex);

        printf("   Token: %s\n", qlex->token->get_string().c_str());
        
    } while( token._id != QUEX_TKN_TERMINATION );

    printf("<terminated>\n");
}

