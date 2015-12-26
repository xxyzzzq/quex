#include "boeck_Lexer.h"
#include <quex/code_base/multi.i>

int 
main(int argc, char** argv) 
{        
    boeck_Lexer   x;
    boeck_Lexer_from_file_name(&x, "empty.txt", "UCS4");
    boeck_Lexer_destruct(&x);

    return 0;
}

