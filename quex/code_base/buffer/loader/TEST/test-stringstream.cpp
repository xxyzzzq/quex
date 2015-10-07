/* PURPOSE: See comment in file 'basic_functionality.c'                      */
#include <quex/code_base/buffer/loader/ByteLoader_stream>
#include <quex/code_base/buffer/loader/ByteLoader_stream.i>
#include <quex/code_base/buffer/loader/ByteLoader.i>
#include <quex/code_base/MemoryManager.i>
#include <basic_functionality.h>
#include <hwut_unit.h>
#include <sstream> 
#include <string> 

int
main(int argc, char** argv)
{
    char               tmp_buffer[1024];
    std::ifstream      fstr("test.txt", std::ios::in);

    hwut_info("ByteLoader: std::stringstring;\n"
              "CHOICES: basic, init-pos;");

    fstr.read(&tmp_buffer[0], TEST_FILE_SIZE);
    tmp_buffer[TEST_FILE_SIZE] = '\0';

    std::string         sbuffer(tmp_buffer);
    std::istringstream  sstr(sbuffer);
    ByteLoader*         me = ByteLoader_stream_new(&sstr);

    hwut_if_choice("basic")    verify_basic_functionality(me);
    hwut_if_choice("init-pos") initial_position(me);

    me->delete_self(me);

    return 0;
}

