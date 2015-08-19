#include "Lexer.h"

#include <stdlib.h>

int main(int argc, char* argv[])
{
    Lexer lex;
    QUEX_NAME(from_file_name)(&lex, argv[1], NULL, false);

    while (1) {
        QUEX_TYPE_TOKEN* t = NULL;
        QUEX_NAME(receive)(&lex, &t);

        if (QUEX_TKN_TERMINATION == t->_id)
            break;

        printf("id=%s text=[%s]\n",
               QUEX_NAME_TOKEN(map_id_to_name)(t->_id),
               t->text);
    }

    QUEX_NAME(destruct)(&lex);

    return 0;
}
