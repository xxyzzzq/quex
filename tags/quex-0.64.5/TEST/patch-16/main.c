#include <stdio.h>
#include "simple.h"
#include "simple-token_ids.h"
#define BUFFER_SIZE 1024
char file_buffer[BUFFER_SIZE];

#ifndef     ENCODING_NAME
#    define ENCODING_NAME (0x0)
#endif

int main(int argc, char** argv) {
	quex_simple qlex;
	QUEX_TYPE_TOKEN token_p;
	char* file = argc == 1 ? "example.txt" : argv[1];
	QUEX_NAME_TOKEN(construct)(&token_p);
	QUEX_NAME(construct_file_name)(&qlex, file, ENCODING_NAME, false);
	QUEX_NAME(token_p_switch)(&qlex, &token_p);
	do {
		QUEX_NAME(receive)(&qlex);
		/* Print out token information            */
#       ifdef PRINT_LINE_COLUMN_NUMBER
		printf("(%i, %i)  \t", (int)token_p._line_n, (int)token_p._column_n);
#       endif
#       ifdef PRINT_TOKEN
		printf("%s \n", QUEX_NAME_TOKEN(get_string)(&token_p, buffer, BufferSize));
#       else
		printf("%s\n", QUEX_NAME_TOKEN(map_id_to_name)(token_p._id));
#       endif
	} while(token_p._id != QUEX_TKN_TERMINATION);

	QUEX_NAME(destruct)(&qlex);
	QUEX_NAME_TOKEN(destruct)(&token_p);
	return 0;
}

