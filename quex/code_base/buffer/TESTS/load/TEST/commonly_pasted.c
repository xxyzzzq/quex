
#include <quex/code_base/test_environment/TestAnalyzer-configuration>
#include <quex/code_base/buffer/lexatoms/LexatomLoader.i>
#include <quex/code_base/buffer/bytes/ByteLoader_Memory>
#include <quex/code_base/buffer/bytes/ByteLoader_Memory.i>
#include <quex/code_base/buffer/Buffer_debug.i>
#include <quex/code_base/buffer/Buffer.i>
#include <quex/code_base/MemoryManager>
#include <quex/code_base/converter_helper/from-unicode-buffer.i>
#include <quex/code_base/single.i>
#include <hwut_unit.h>

static const QUEX_TYPE_LEXATOM  PseudoFile[] = {
   1,  2,  3,  4,  5,  6,  7,  8,  9,  10, 11, 12, 13, 14, 15, 16, 
   17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32
};

#define PSEUDO_FILE_SIZE  sizeof(PseudoFile)

static ptrdiff_t
verify_content(QUEX_NAME(Buffer)* me)
{
    QUEX_TYPE_LEXATOM  expected;
    QUEX_TYPE_LEXATOM* p;
    ptrdiff_t            count = 0;

    /* If end_p does not stand on buffer boarder, then it must stand according
     * to the 'lexatom_index_begin' at the end of the pseudo files content.*/
    if( me->input.end_p != me->_memory._back ) {
        hwut_verify(me->input.end_p - &me->_memory._front[1] + me->input.lexatom_index_begin
                    == sizeof(PseudoFile)/sizeof(PseudoFile[0]));
    }
    /* Make sure that the content has been loaded properly. From the 
     * variable 'pseudo_file' it can be previewed what the content is 
     * supposed to be.                                                       */
    for(p=&me->_memory._front[1]; p != me->input.end_p ; ++p) {
        expected = PseudoFile[me->input.lexatom_index_begin + p - &me->_memory._front[1]];
        hwut_verify(*p == expected);
        ++count;
    }
    hwut_verify(count == me->input.end_p - &me->_memory._front[1]);

    return count;
}
