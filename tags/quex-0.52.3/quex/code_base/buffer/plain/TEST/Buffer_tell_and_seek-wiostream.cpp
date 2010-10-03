#define QUEX_SETTING_BUFFER_MIN_FALLBACK_N 0
#include <quex/code_base/buffer/TEST/Buffer_test_common.i>
#include "test-helper.h"

#include <sstream>

int
main(int argc, char** argv)
{
    using namespace std;
    if( cl_has(argc, argv, "--hwut-info") ) {
        printf("Tell and Seek: wiostream;\n");
        return 0;
    }
    std::wstringstream    sh;
    QUEX_NAME(Buffer)     buffer;
    size_t                SeekIndices[] = { 5, 9, 3, 8, 2, 15, 25, 7, 
                                            19, 4, 6, 20, 11, 0, 
                                            23, 18, 12, 21, 17, 27, 16, 26, 
                                            14, 24, 10, 13, 1, 22, 999 };

    __quex_assert(sizeof(QUEX_TYPE_CHARACTER) == sizeof(wchar_t));

    sh << L"Fest gemauert in der Erden";
    QUEX_NAME(Buffer_construct)(&buffer, &sh, 0x0, 5, 0x0, 0x0, 0, false);

    test_seek_and_tell(&buffer, SeekIndices);
}
