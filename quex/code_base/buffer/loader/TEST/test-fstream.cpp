/* PURPOSE: See comment in file 'basic_functionality.c'                      */
#include <quex/code_base/buffer/loader/ByteLoader_stream>
#include <quex/code_base/buffer/loader/ByteLoader_stream.i>
#include <quex/code_base/buffer/loader/ByteLoader.i>
#include <quex/code_base/MemoryManager.i>
#include <basic_functionality.h>
#include <hwut_unit.h>
#include <iostream>

int
main(int argc, char** argv)
{
    ByteLoader*  me;
    hwut_info("ByteLoader_stream: std::fstream -- basic functionality;\n");

    hwut_verify(ByteLoader_stream_new_from_file_name("not-existing-file.txt") == (ByteLoader*)0);
    me = ByteLoader_stream_new_from_file_name("test.txt");

    verify_basic_functionality(me);

    me->delete_self(me);

    return 0;
}

