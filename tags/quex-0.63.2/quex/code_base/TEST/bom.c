#include <stdio.h>
#define QUEX_NAME(X) (X)
#include <quex/code_base/bom>
#include <quex/code_base/bom.i>
#include <support/C/hwut_unit.h>


int
main(int argc, char** argv)
{
    const char* file_names[] = { "data/bocu1.txt", 
                                 "data/gb18030.txt",
                                 "data/scsu.txt",
                                 "data/utf16be.txt",
                                 "data/utf16le.txt",
                                 "data/utf32be.txt",
                                 "data/utf32le.txt",
                                 "data/utf7.txt",
                                 "data/utf8.txt",
                                 0x0,
    };
    const char**   iterator;
    FILE*          fh = 0x0;
    QUEX_TYPE_BOM  bom = QUEX_BOM_NONE;

    hwut_info("BOM Snap: FILE\n");

    for(iterator = file_names; *iterator != 0x0; ++iterator ) {
        fh = fopen(*iterator, "rb");
        bom = quex_bom_snap(fh);

        printf("%s\n", *iterator);
        printf("   CODEC: %s\n", quex_bom_name(bom));
        printf("   BYTES: ");
        while( ! feof(fh) )
        {
            printf("%02X.", (int)fgetc(fh));
        }
        printf("\n");
        fclose(fh);
    }
}
