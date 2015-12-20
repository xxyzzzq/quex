#include <stdio.h>    
#include <hwut_unit.h>    

#include "EasyLexer.h"

#ifndef     ENCODING_NAME
#    define ENCODING_NAME (0x0)
#endif

static void print_token(quex_Token* token_p);

int 
main(int argc, char** argv) 
{        
    quex_Token*      token_p = NULL;
    size_t           number_of_tokens = 0;
    quex_EasyLexer   qlex;
    const char*      file_name; 
    QUEX_NAME(Mode)* mode;

    hwut_info("Testing states with no hole in transition map;\n"
              "CHOICES: BEGIN-1, BEGIN-many, MIDDLE-1, MIDDLE-many, END-1, END-many;");

    hwut_if_choice("BEGIN-1")    { file_name = "BEGIN-1.txt"; mode = &QUEX_NAME(BEGIN); }
    hwut_if_choice("BEGIN-many") { file_name = "BEGIN-many.txt"; mode = &QUEX_NAME(BEGIN); }
    hwut_if_choice("MIDDLE-1")    { file_name = "MIDDLE-1.txt"; mode = &QUEX_NAME(MIDDLE); }
    hwut_if_choice("MIDDLE-many") { file_name = "MIDDLE-many.txt"; mode = &QUEX_NAME(MIDDLE); }
    hwut_if_choice("END-1")    { file_name = "END-1.txt"; mode = &QUEX_NAME(END); }
    hwut_if_choice("END-many") { file_name = "END-many.txt"; mode = &QUEX_NAME(END); }

    quex_EasyLexer_from_file_name(&qlex, file_name, ENCODING_NAME);
    QUEX_NAME(enter_mode)(&qlex, mode);

    printf("[START]\n");

    do {
        quex_EasyLexer_receive(&qlex, &token_p);

        print_token(token_p);

        ++number_of_tokens;

    } while( token_p->_id != QUEX_TKN_TERMINATION );

    quex_EasyLexer_destruct(&qlex);

    printf("[END] number of token = %i\n", number_of_tokens);
    return 0;
}

static void
print_token(quex_Token* token_p)
{
#   ifdef PRINT_TOKEN
    const size_t    BufferSize = 1024;
    char            buffer[1024];
#   endif

#   ifdef PRINT_LINE_COLUMN_NUMBER
    printf("(%i, %i)  \t", (int)token_p->_line_n, (int)token_p->_column_n);
#   endif

#   ifdef PRINT_TOKEN
    printf("%s \n", QUEX_NAME_TOKEN(get_string)(token_p, buffer, BufferSize));
#   else
    printf("%s\n", QUEX_NAME_TOKEN(map_id_to_name)(token_p->_id));
#   endif
}
