#include <ctime>
#include <cstdlib>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <c_lexer>

using namespace std;

size_t    get_file_size(const char*);
void      print_date_string();
size_t    count_token_n(std::FILE*);
float     report(clock_t StartTime, float RepetitionN, size_t FileSize, size_t CharacterSize);
void      final_report(float TimePerRun, float RefTimePerRun, const char* Filename, 
                       size_t FileSize, size_t TokenN, float RepetitionN);

void 
final_report(float TimePerRun, float RefTimePerRun, const char* FileName, size_t FileSize, size_t TokenN, float RepetitionN)
{
    const float  CharN          = (float)(FileSize) / (CHARACTER_SIZE);
    const float  CycleTime      = 1.0 / (CPU_FREQ_MHZ * 1e6);
    const float  TimePerChar    = TimePerRun  / CharN;
    const float  CCC            = TimePerChar / CycleTime;
    const float  TimePerToken   = TimePerRun  / float(TokenN);
    const float  CCT            = TimePerToken / CycleTime;
    const float  RefTimePerChar  = RefTimePerRun  / CharN;
    const float  RefCCC          = RefTimePerChar / CycleTime;
    const float  RefTimePerToken = RefTimePerRun  / float(TokenN);
    const float  RefCCT          = RefTimePerToken / CycleTime;

    cout << "//Result:\n";
    cout << "//   Time / Run:          " << (TimePerRun - RefTimePerRun)   << endl;
    cout << "//   Time / Char:         " << (TimePerChar - RefTimePerChar) << endl;
    cout << "//   Clock Cycles / Char: " << (CCC - RefCCC)                 << endl;
    cout << "{" << endl;
    cout << "   quex_version = {" << QUEX_VERSION << "}, " << endl;
    cout << "   cpu_name     = {" << CPU_NAME << "}, " << endl;
    cout << "   cpu_code     = {" << CPU_CODE << "}, " << endl;
    cout << "   cpu_freq_mhz = {" << CPU_FREQ_MHZ << "}, " << endl;
    cout << "   cc_name      = {" << CC_NAME << "}, " << endl;
    cout << "   cc_version   = {" << CC_VERSION << "}, " << endl;
    cout << "   cc_opt_flags = {" << CC_OPTIMIZATION_FLAGS << "}, " << endl;
    cout << "   os_name      = {" << OS_NAME << "}, " << endl;
    cout << "   email        = {" << EMAIL << "}, " << endl;
    print_date_string();
    cout << "   file_name    = {" << FileName << "}, " << endl;
    cout << "   file_size    = {" << FileSize << "}, " << endl;
    cout << "   char_size    = {" << CHARACTER_SIZE << "}, " << endl;
    cout << "   buffer_size  = {" << QUEX_SETTING_BUFFER_SIZE << "}, " << endl;
#       ifdef QUEX_OPTION_LINE_NUMBER_COUNTING
    cout << "   line_count   = {true}," << endl;
#       else
    cout << "   line_count   = {false}," << endl;
#       endif
#       ifdef QUEX_OPTION_COLUMN_NUMBER_COUNTING
    cout << "   column_count = {true}," << endl;
#       else
    cout << "   column_count = {false}," << endl;
#       endif
    cout << "   note         = {" << NOTE << "}, " << endl;
    // Result
    cout << "   repetition_n               = {" << (unsigned int)(RepetitionN) << "}, " << endl;
    cout << "   time_per_repetition        = {" << (TimePerRun - RefTimePerRun) << "}," << endl;
    cout << "   token_n                    = {" << TokenN << "}, " << endl;
    cout << "   clock_cycles_per_character = {" << (CCC - RefCCC) << "}, " << endl;
    cout << "   clock_cycles_per_token     = {" << (CCT - RefCCT) << "}, " << endl;
    cout << "}\n" << endl;
}


float
report(clock_t StartTime, float RepetitionN, size_t FileSize, size_t CharacterSize)
{ 
    using namespace std;

    const clock_t EndTime    = clock();
    const float   TimeDiff   = (float)(EndTime - StartTime) / (float)CLOCKS_PER_SEC;
    const float   TimePerRun = TimeDiff / RepetitionN;

    cout << "//    Total Time:  " << TimeDiff          << " [sec]" << endl;
    cout << "//    Runs:        " << (long)RepetitionN << " [1]"   << endl;
    cout << "//    TimePerRun:  " << TimePerRun        << " [sec]" << endl;

    const float  CharN          = FileSize / CHARACTER_SIZE;
    const float  CycleTime      = 1.0 / (CPU_FREQ_MHZ * 1e6);
    const float  TimePerChar    = TimePerRun  / CharN;
    const float  CCC            = TimePerChar / CycleTime;

    cout << "//    Time / Char:         " << TimePerChar << endl;
    cout << "//    Clock Cycles / Char: " << CCC         << endl;

    return TimePerRun;
}

size_t
count_token_n(std::FILE* fh)
{
    using namespace std;
    quex::c_lexer*  qlex = new quex::c_lexer(fh);
    quex::token*    TokenP;
    int token_n = 0;

    // (*) loop until the 'termination' token arrives
    for(token_n=0; ; ++token_n) {
        qlex->get_token(&TokenP);
        if( TokenP->type_id() == quex::TKN_TERMINATION ) break;
    } 
    cout << "//TokenN: " << token_n << " [1]"   << endl;
    return token_n;
}

size_t
get_file_size(const char* Filename)
{
    using namespace std;
    struct stat s;
    stat(Filename, &s);
    cout << "//FileSize: " << s.st_size << " [Byte] = "; 
    cout << float(s.st_size) / float(1024) << " [kB] = ";
    cout << float(s.st_size) / float(1024*1024) << " [MB]." << endl;
    return s.st_size;
}

void
print_date_string()
{

    std::time_t  current_time     = time(NULL); 
    struct tm*   broken_down_time = std::gmtime(&current_time);
    
    std::cout << "   year         = {" << broken_down_time->tm_year + 1900   << "}," << endl;
    std::cout << "   month        = {" << broken_down_time->tm_mon  + 1    << "}," << endl;
    std::cout << "   day          = {" << broken_down_time->tm_mday        << "}," << endl;
}
