/* PURPOSE: See comment in file 'basic_functionality.c'                      */
#include <basic_functionality.h>
#include <quex/code_base/buffer/loader/ByteLoader_FILE>
#include <quex/code_base/buffer/loader/ByteLoader_FILE.i>
#include <quex/code_base/buffer/loader/ByteLoader.i>
#include <quex/code_base/MemoryManager.i>
#include <hwut_unit.h>

int
main(int argc, char** argv)
{
    QUEX_NAME(ByteLoader)*  me;
    hwut_info("QUEX_NAME(ByteLoader): FILE;\n"
              "CHOICES: basic, init-pos;");

    hwut_verify(QUEX_NAME(ByteLoader_FILE_new_from_file_name)("not-existing-file.txt") == (QUEX_NAME(ByteLoader)*)0);
    hwut_verify(QUEX_NAME(ByteLoader_FILE_new)(NULL, false) == (QUEX_NAME(ByteLoader)*)0);
    me = QUEX_NAME(ByteLoader_FILE_new_from_file_name)("test.txt");

    hwut_if_choice("basic")    verify_basic_functionality(me);
    hwut_if_choice("init-pos") initial_position(me);

    me->delete_self(me);

    return 0;
}

