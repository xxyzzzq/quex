#ifndef __INCLUDE_GUARD_BUFFER_UNIT_TEST_HEADER__
#define __INCLUDE_GUARD_BUFFER_UNIT_TEST_HEADER__

#include<string>
// __QUEX_OPTION_UNIT_TEST: enables functions and features that are
//                          only available for testing.
#include<../buffer>
#include<cassert>

using namespace std;

template<class Buffer> inline 
std::string
read_backward_until_begin_of_buffer(Buffer& x) {
    std::string result;

    cout << "\n(*) read to begin of buffer\n";
    while( 1 + 1 == 2 ) {
        const int tmp = x.get_backward();
        // See file README.txt in directory ./quex/buffer      
        if( x.is_begin_of_file() ) { break; /* we are at the end, simply do get_backward again */ }
        else if( x.is_begin_of_buffer() ) { 
            assert(tmp == x.BLC);
            std::cout << "begin of buffer\n";
            {x.decrement(); x.mark_lexeme_start(); x.increment(); }
            return result;
        }
        else {
            if( tmp == ' ' ) {x.decrement(); x.mark_lexeme_start(); x.increment(); }
            result += tmp;
        }
    }
}

template<class Buffer> inline 
std::string
read_forward_until_end_of_buffer(Buffer& x) 
{
    std::string result;

    cout << "\n(*) read to end of buffer\n";
    while( 1 + 1 == 2 ) {
        const int tmp = x.get_forward();
        //
        // x.show_content();
        //
        // See file README.txt in directory ./quex/buffer      
        if( x.is_end_of_file() ) { break; /* we are at the end, simply do get_forward again */ }
        else if( x.is_end_of_buffer() ) {
            assert(tmp == x.BLC);
            std::cout << "end of buffer\n";
            return result;
        }
        else {
            if( tmp == ' ' ) {x.decrement(); x.mark_lexeme_start(); x.increment(); }
            result += tmp;
        }
    }
    return result;
}

template<class Buffer> inline 
std::string 
read_to_end_of_file(Buffer& x) {
    std::string result;

    cout << "\n(*) read to end of file\n";
    while( 1 + 1 == 2 ) {
        const int tmp = x.get_forward();
        //
        // std::cout << "input = " << char(tmp) << endl;
        // x.show_content();
        //
        // See file README.txt in directory ./quex/buffer      
        if( x.is_end_of_file() ) { break; /* we are at the end, simply do get_forward again */ }
        else if( tmp == x.BLC ) {
            // std::cout << "try load";
            if( x.load_forward() == -1 ) break;
            // std::cout << " - success\n";
        }
        else {
            if( tmp == ' ' ) {x.decrement(); x.mark_lexeme_start(); x.increment(); }
            result += tmp;
        }
    }
    std::cout << "- end of file\n";
    return result;
}

template<class Buffer> inline 
std::string
read_to_begin_of_file(Buffer& x) {    
    std::string result;

    cout << "\n(*) read to begin of file\n";
    while( 1 + 1 == 2 ) {
        const int tmp = x.get_backward();
        //
        // x.show_content();
        //
        // See file README.txt in directory ./quex/buffer      
        if( x.is_begin_of_file() ) { break; /* we are at the end, simply do get_backward again */ }
        else if( tmp == x.BLC ) {
            // std::cout << "try load";
            if( x.load_backward() == -1 ) break;
            // std::cout << " - success\n";
            // x.x_show_content();
        }
        else {
            if( tmp == ' ' ) {x.decrement(); x.mark_lexeme_start(); x.increment(); }
            result += tmp;
        }
    }
    std::cout << "- begin of file\n";
    {x.decrement(); x.mark_lexeme_start(); x.increment(); }
    return result;
}

void test_istream(int ContentSz, int BackupSz);
void test_stdio(int ContentSz, int BackupSz);

#endif // __INCLUDE_GUARD_BUFFER_UNIT_TEST_HEADER__
