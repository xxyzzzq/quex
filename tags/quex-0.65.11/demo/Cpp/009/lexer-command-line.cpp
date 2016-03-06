/* Lexical Analyzer fed from a Command Line
 * -----------------------------------------
 *
 * In this example, user interaction results in a command line which is then
 * lexically analyzed. This example requires the 'GNU readline' library to
 * be installed.
 *_____________________________________________________________________________
 *
 *  EXAMPLE:
 *  
 *    Ascii-codec command line:
 *
 *          > ./lexer-command-line
 *        
 *          type here: A message of a kilobyte
 *              read: 24 [byte]
 *              Token: ARTICLE 'A'
 *              Token: SUBJECT 'message'
 *              Token: PREPOSITION 'of'
 *              Token: ARTICLE 'a'
 *              Token: SUBJECT 'kilobyte'
 *              Token: <TERMINATION> ''
 *          type here: starts with a single bit
 *              read: 25 [byte]
 *              Token: SUBJECT 'starts'
 *              Token: PREPOSITION 'with'
 *              Token: ARTICLE 'a'
 *              Token: ATTRIBUTE 'single'
 *              Token: STORAGE_UNIT 'bit'
 *              Token: <TERMINATION> ''
 *          type here: ^C
 *        
 *    Similarly, the UTF8 command line parser may be used:
 *        
 *          > ./lexer-command-line-utf8
 *          
 *_____________________________________________________________________________
 *
 * (C) Frank-Rene Schaefer                                                   */

#include <stdio.h>
#if ! defined(WITH_UTF8)
#   include <LexAscii>
#   define  LEXER_CLASS   LexAscii
#   define  CODEC         NULL
#else
#   include <LexUtf8>
#   define  LEXER_CLASS   LexUtf8
#   define  CODEC         "UTF8"
#endif


int 
main(int argc, char** argv) 
{        
    using namespace quex;
    using namespace std;
    Token*                   token;
    LEXER_CLASS*             qlex;   
    char                     buffer[4096];
    ssize_t                  received_n;
    QUEX_NAME(LexatomLoader)* filler = QUEX_NAME(LexatomLoader_new_DEFAULT)(NULL, CODEC);

    qlex = new LEXER_CLASS(filler);

    while( 1 + 1 == 2 ) {
        printf("type here: ");

		cin.getline((std::basic_istream<char>::char_type*)&buffer[0], 4096);
        received_n = cin.gcount();

        /* Last received byte is the terminating zero! => -1 !               
         *                                                                   */
        printf("    read: %i [byte]\n", received_n - 1);

        qlex->reset();

        /* NOTE: If the character index of the pipe needs to be traced properly
         * the 'newline' character needs to be inserted manually, because, it
         * is cut out of the stream by 'getline()'. Trick: replace the
         * terminating zero (which is not needed by the engine) by the line's
         * newline, i.e:                                
         *
         *            buffer[received_n-1] = '\n';      
         *            qlex->buffer.fill( ... &buffer[received_n]);                 
         *                                                                   */
        qlex->buffer.fill(&qlex->buffer, &buffer[0], &buffer[received_n - 1]);

        token = qlex->token;
        do {
            qlex->receive();
            printf("   Token: %s\n", token->get_string().c_str()); 
        } while( token->_id != QUEX_TKN_TERMINATION && token->_id != QUEX_TKN_BYE );
    }
        
    delete qlex; 
    filler->delete_self(filler);
    printf("<terminated>\n");
    return 0;
}


