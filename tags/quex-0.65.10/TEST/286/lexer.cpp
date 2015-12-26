#include "iostream"
#include "tokenizer_it"

int main(int argc, char** argv)
{
	using namespace std;
	using namespace quex;

	quex::Token              token;
    QUEX_NAME(BufferFiller)* filler = QUEX_NAME(BufferFiller_new_DEFAULT)(NULL, "UTF8");
	quex::tokenizer_it       qlex(filler); 
    uint8_t*                 begin_p;
    const uint8_t*           end_p;
    size_t                   received_n;

	qlex.token_p_swap(&token);
	while (cin) {
		qlex.buffer.fill_prepare(&qlex.buffer, (void**)&begin_p, (const void**)&end_p);
        // printf("#fr: %p (%i)\n", begin_p, (size_t)(end_p - begin_p));
		// Read a line from standard input

		cin.getline((std::basic_istream<char>::char_type*)begin_p, 
                    (size_t)(end_p - begin_p)); 

        received_n = cin.gcount();
		if( ! received_n ) return 0;

        /* getline() cuts the newline. To be able to trace the character index
         * correctly, the newline needs to be re-inserted manually.          */
        begin_p[received_n-1] = '\n';

        printf("line: (%i) [", received_n); 
        for(int i=0; i < received_n; ++i) printf("%02X.", (int)begin_p[i]);
        printf("]\n");

		qlex.buffer.fill_finish(&qlex.buffer, &begin_p[received_n]);

		while (true) {
			const QUEX_TYPE_TOKEN_ID TokenID = qlex.receive();

			if (TokenID == QUEX_TKN_TERMINATION)
				break;
			else if (TokenID == QUEX_TKN_EOS) {
				cout << endl;
			} else {
				int offset = qlex.tell() - token.text.size();
				cout << offset << '\t' << quex::unicode_to_char(token.text) << endl;
			}
		}
	}
    filler->delete_self(filler);
}

