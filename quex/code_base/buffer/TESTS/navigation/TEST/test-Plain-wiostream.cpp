#include <hwut_unit.h>
#include <basic_functionality.h>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/MemoryManager.i>


#include <sstream>

using namespace std;

QUEX_NAMESPACE_MAIN_OPEN
static void test(bool BinaryF, size_t BPC);
QUEX_NAMESPACE_MAIN_CLOSE

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
    hwut_if_choice("linear")   QUEX_NAMESPACE_MAIN::test(true, BPC);
    hwut_if_choice("stepping") QUEX_NAMESPACE_MAIN::test(false, BPC);

    return 0;
}

QUEX_NAMESPACE_MAIN_OPEN
static void
test(bool BinaryF, size_t BPC)
{
    QUEX_NAME(Buffer)         buffer;
    std::wstringstream        sh;
    ByteLoader*               byte_loader;
    QUEX_NAME(BufferFiller*)  filler;
    const size_t              MemorySize  = true ? 5 : 16;
    QUEX_TYPE_CHARACTER       memory[MemorySize];

    sh << L"Fest gemauert in der Erden\n";
    sh.seekg(0);
    byte_loader = ByteLoader_stream_new(&sh);
    hwut_verify(byte_loader);

    byte_loader->binary_mode_f = BinaryF;
    filler = QUEX_NAME(BufferFiller_Plain_new)(byte_loader);
    hwut_verify(filler);

    QUEX_NAME(Buffer_construct)(&buffer, filler, &memory[0], MemorySize, 0, E_Ownership_EXTERNAL);

    /* REFERENCE file and INPUT file are the SAME.                           */
    hwut_verify(basic_functionality(&buffer, find_reference("examples/festgemauert")));

    filler->delete_self(filler);
}

QUEX_NAMESPACE_MAIN_CLOSE
