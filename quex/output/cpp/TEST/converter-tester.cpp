#include <stdio.h>
#include "converter-tester.h"

int
main(int argc, char** argv)
{
    using namespace quex;

    const size_t         Start      = 0x0;
    const size_t         CharacterN = 255;
    QUEX_TYPE_CHARACTER  source[256];
    uint8_t              drain[4096];
    uint8_t              drain_ref[4096];

    /* Fill source buffer with all available characters */
    for(int i=Start; i < Start + CharacterN; ++i) source[i-Start] = i;

    /* Convert the whole array */
    uint8_t*     drain_end = CONVERT_TO_UTF8(source, CharacterN, (uint8_t*)drain, 4095);
    const int    Size = (int)(drain_end - (uint8_t*)drain);
    *drain_end = '\0'; /* terminating zero */

    printf("Result (%i):\n", Size);
    for(int i=0; i<Size; ++i) {
        if( i % 16 == 0 ) printf("\n");
        printf("%02X.", (int)(drain[i]));
    }
    printf("\n");
    
#   if 0
    FILE* fhi = fopen("for-reference.txt", "wb");
    fwrite(source, 1, CharacterN, fhi);
    fclose(fhi);
  
    FILE* fh_out  = fopen("tmp.txt", "wb");
    fwrite(drain, 1, Size, fh_out);
    fclose(fh_out);
#   endif

    FILE* fh = fopen("reference-" __QUEX_CODEC "-to-utf8.txt", "rb");
    const size_t RefSize = fread(drain_ref, 1, 4096, fh);

    if( RefSize != Size ) {
        printf("Reference Size = %i, Size = %i --> Error\n", (int)RefSize, (int)Size);
        return -1;
    }

    /* Compare the output */
    printf("Check result (no response == OK)\n");
    for(int i=0; i<Size; ++i) {
        if( drain[i] != drain_ref[i] ) {
            printf("Error at position '%i'.\n", i);
            break;
        }
    }
    fclose(fh);
}
