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
    assert(sizeof(QUEX_TYPE_CHARACTER) == sizeof(wchar_t));

    sh << L"Fest gemauert in der Erden";

    QuexBuffer                             buffer;
    size_t    SeekIndices[] = { 5, 9, 3, 8, 2, 15, 25, 7, 19, 4, 6, 20, 11, 0, 
                                23, 18, 12, 21, 17, 27, 16, 26, 14, 24, 10, 13, 1, 22, 999 };

    QuexBufferFiller_Plain<wstringstream>* filler = QuexBufferFiller_Plain_new(&sh);
    buffer.filler = (quex::__QuexBufferFiller_tag*)filler;
    QuexBufferMemory_init(&(buffer._memory), MemoryManager_BufferMemory_allocate(5), 5);      
    QuexBuffer_init(&buffer, /* OnlyResetF */false);

    test_seek_and_tell(&buffer, SeekIndices);
}
