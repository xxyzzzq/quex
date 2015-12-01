/* Stdandard-Input-Based Lexical Analyzer
 * --------------------------------------
 *
 * This application implements a lexical analyzer that reads from the Standard
 * Input, often referred to as 'stdin'. It does so by means of a POSIX byte
 * loader (while a FILE byte loader may equally do). The lexical analysis
 * terminates with the termination character on the standard input 'Ctrl-D'.
 *_____________________________________________________________________________
 *
 * EXAMPLE:
 *
 *  Under Unix/Linux use the 'pipe' character to redirect the output of a 
 *  command to the standard input of the lexical analyzer.
 *  
 *     > cat example-feed.txt | ./lexer-stdin
 *  
 *_____________________________________________________________________________
 *
 * (C) Frank-Rene Schaefer                                                   */

#include <stdio.h>
#if ! defined(WITH_UTF8)
#   include <LexAscii.h>
#   define  LEXER_CLASS   quex_LexAscii
#   define  CODEC         NULL
#else
#   include <LexUtf8.h>
#   define  LEXER_CLASS   quex_LexUtf8
#   define  CODEC         "UTF8"
#endif

static void  print_token(quex_Token*  token);
static void  announce(void);

int 
main(int argc, char** argv) 
{        
    quex_Token*     token;
    LEXER_CLASS     qlex;   


    QUEX_NAME(ByteLoader)* loader = QUEX_NAME(ByteLoader_POSIX_new)(connected_fd);

    announce();

    if( connected_fd == -1 ) {
        printf("server: accept() terminates with failure.\n");
        sleep(1);
        return true;
    }

    QUEX_NAME(ByteLoader_seek_disable)(loader);

    /* A handler for the case that nothing is received over the line. */
    loader->on_nothing = self_on_nothing; 

    QUEX_NAME(from_ByteLoader)(&qlex, loader, CODEC);


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
