#include <iostream>
#include <sstream>

#include <quex/code_base/buffer/plain/fixed_size_character_stream>
#include <test-core.h>

using namespace quex;
using namespace std;

template <class Buffer> inline void
test_this(Buffer& x)
{
    
    cout << "<" << read_to_end_of_file(x) << ">" << endl;
    x.x_show_content();

    cout << "<" << read_to_begin_of_file(x) << ">" << endl;
    x.x_show_content();

    cout << "<" << read_forward_until_end_of_buffer(x) << ">" << endl;
    x.x_show_content();

    cout << "\n(*) load_forward:\n";
    x.load_forward();
    x.x_show_content();

    cout << "<" << read_forward_until_end_of_buffer(x) << ">" << endl;
    x.x_show_content();

    cout << "\n(*) load_forward:\n";
    x.load_forward();
    x.x_show_content();

    cout << "<" << read_to_end_of_file(x) << ">" << endl;
    x.x_show_content();

    cout << "<" << read_backward_until_begin_of_buffer(x) << ">" << endl;
    x.x_show_content();

    cout << "\n(*) load_backward:\n";
    x.load_backward();
    x.x_show_content();

    cout << "<" << read_backward_until_begin_of_buffer(x) << ">" << endl;
    x.x_show_content();

    cout << "\n(*) load_backward:\n";
    x.load_backward();
    x.x_show_content();

    cout << "<" << read_to_begin_of_file(x) << ">" << endl;
    x.x_show_content();

    cout << "<" << read_to_end_of_file(x) << ">" << endl;
    x.x_show_content();
}

void
test_istream(int ContentSz, int BackupSz)
{
    istringstream ifs("Im Wald steht ein Baum.");

    // '+2' because of two positions for begin and end of buffer
    fixed_size_character_stream_plain<istringstream, char>  input_strategy(&ifs);
    quex::buffer<char>                         x(&input_strategy, ContentSz + 2, BackupSz, '\0'); 

    cout << "-(total size = " << ContentSz << ", border = " << BackupSz;
    cout << ")-------------------------------------------\n";
    test_this(x);
}

void
test_stdio(int ContentSz, int BackupSz)
{
    std::FILE*       fh = fopen("test.txt", "w");
    fprintf(fh, "Im Wald steht ein Baum.");
    fclose(fh);
    fh = fopen("test.txt", "r");
    setvbuf(fh, 0x0, _IONBF, 0);   // disable buffering
    __quex_assert(fh != 0x0);
    //
    // '+2' because of two positions for begin and end of buffer
    fixed_size_character_stream_plain<std::FILE, char>  input_strategy(fh);
    quex::buffer<char>                     x(&input_strategy, ContentSz + 2, BackupSz, 0); 

    cout << "-(total size = " << ContentSz << ", border = " << BackupSz;
    cout << ")-------------------------------------------\n";

    test_this(x);
}


