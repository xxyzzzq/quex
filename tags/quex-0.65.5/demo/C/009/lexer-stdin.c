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
 *  Or, respectively for a UTF8 lexer:
 *
 *     > cat example-feed-utf8.txt | ./lexer-stdin-utf8
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

int 
main(int argc, char** argv) 
{        
    quex_Token*            token;
    LEXER_CLASS            qlex;   
    QUEX_NAME(ByteLoader)* loader = QUEX_NAME(ByteLoader_POSIX_new)(0); /* 0 = stdin */

    QUEX_NAME(ByteLoader_seek_disable)(loader);

    QUEX_NAME(from_ByteLoader)(&qlex, loader, CODEC);

    token = qlex.token;
    do {
        (void)QUEX_NAME(receive)(&qlex);
        print_token(token);
    } while( token->_id != QUEX_TKN_TERMINATION && token->_id != QUEX_TKN_BYE );
        
    QUEX_NAME(destruct)(&qlex);
    loader->delete_self(loader);
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

