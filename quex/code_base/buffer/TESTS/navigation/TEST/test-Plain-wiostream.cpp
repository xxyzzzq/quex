#include <hwut_unit.h>
#include <basic_functionality.h>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/MemoryManager.i>

static void test(bool BinaryF, size_t BPC);

#include <sstream>

using namespace std;

int
main(int argc, char** argv)
{
    const size_t   BPC = sizeof(QUEX_TYPE_CHARACTER);
    if( argc > 1 && strcmp(argv[1], "--hwut-info") == 0 ) {
        printf("Buffer Tell&Seek: BufferFiller_Plain (BPC=%i, FALLBACK=%i);\n", 
               BPC, QUEX_SETTING_BUFFER_MIN_FALLBACK_N);
        printf("CHOICES: linear, stepping;\n"
               "SAME;\n");
        return 0;
    }
    hwut_if_choice("linear")   test(true, BPC);
    hwut_if_choice("stepping") test(false, BPC);

    return 0;
}

static void
test(bool BinaryF, const char* FileStem)
{
    QUEX_NAME(Buffer)         buffer;
    std::wstringstream        sh;
    QUEX_NAME(Buffer)         buffer;
    ByteLoader*               byte_loader;
    QUEX_NAME(BufferFiller*)  filler;
    const size_t              MemorySize  = true ? 5 : 16;
    QUEX_TYPE_CHARACTER       memory[MemorySize];

    sh << L"Fest gemauert in der Erden";
    byte_loader = ByteLoader_stream_new(&sh);
    hwut_verify(byte_loader);

    byte_loader->binary_mode_f = BinaryF;
    filler = QUEX_NAME(BufferFiller_Plain_new)(byte_loader);
    hwut_verify(filler);

    QUEX_NAME(Buffer_construct)(&buffer, filler, &memory[0], MemorySize, 0, E_Ownership_EXTERNAL);

    /* REFERENCE file and INPUT file are the SAME.                           */
    hwut_verify(basic_functionality(&buffer, find_reference("festgemauert")));

    filler->delete_self(filler);
}

