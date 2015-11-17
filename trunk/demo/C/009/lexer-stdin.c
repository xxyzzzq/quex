#include <stdio.h>
#include <LexAscii.h>

static void  print_token(quex_Token*  token);
static void  announce(void);

int 
main(int argc, char** argv) 
{        
    quex_Token*     token;
    quex_LexAscii   qlex;   

    announce();

    QUEX_NAME(from_FILE)(&qlex, stdin, NULL, true);

    do {
        QUEX_NAME(receive)(&qlex, &token);
        print_token(token);
    } while( token->_id != QUEX_TKN_TERMINATION && token->_id != QUEX_TKN_BYE );
        
    QUEX_NAME(destruct)(&qlex);
    return 0;
}

static void
print_token(quex_Token*  token)
{
    size_t PrintBufferSize = 1024;
    char   print_buffer[1024];

    printf("   Token: %s\n", QUEX_NAME_TOKEN(get_string)(token, print_buffer, 
                                                         PrintBufferSize));
}

static void  announce(void)
{
    printf("Please, type an arbitrary sequence of the following:\n"
           "-- One of the words: 'hello', 'world', 'hallo', 'welt', 'bonjour', 'le monde'.\n"
           "-- An integer number.\n"
           "-- The word 'bye' in order to terminate.\n"
           "Please, terminate each line with pressing [enter].\n");
}
