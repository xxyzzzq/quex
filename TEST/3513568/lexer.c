#include "boeck_Lexer.h"
#include <quex/code_base/Multi.i>

int 
main(int argc, char** argv) 
{        
    boeck_Lexer   x;
    boeck_Lexer_construct_file_name(&x, "empty.txt", "UCS4", false);
    boeck_Lexer_destruct(&x);

    return 0;
}

