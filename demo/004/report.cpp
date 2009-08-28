#include <ctime>
#include <cstdlib>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <cstdio>
#include <iostream>

#include "token-ids.h"
#if defined(ANALYZER_GENERATOR_FLEX)
#else
#    include "c_lexer"
#endif
using namespace std;

#define QUOTE_THIS(NAME) #NAME

size_t    get_file_size(const char*, bool SilentF=false);
void      print_date_string();
size_t    count_token_n(std::FILE*);
double    report(clock_t StartTime, double RepetitionN, size_t FileSize, size_t CharacterSize);
void      final_report(double TimePerRun, double RefTimePerRun, const char* ThisExecutableName, const char* Filename, 
                       size_t FileSize, size_t TokenN, double RepetitionN);


void 
final_report(double      TimePerRun,              double      RefTimePerRun, 
             const char* ThisExecutableName,      const char* FileName, 
             size_t      FileSize, size_t TokenN, double      RepetitionN)
{
    using namespace std;
    const double  CharN          = (double)(FileSize) / (CHARACTER_SIZE);
    const double  CycleTime      = 1.0 / double(CPU_FREQ_MHZ) * 1e-6;
    //
    const double  TimePerChar    = TimePerRun  / CharN;
    const double  CCC            = TimePerChar / CycleTime;
    const double  RefTimePerChar = RefTimePerRun  / CharN;
    const double  RefCCC         = RefTimePerChar / CycleTime;

    double  TimePerToken = 0;
    double  CCT          = 0;
    double  RefTimePerToken = 0;
    double  RefCCT          = 0;

    if( TokenN == 1 ) { 
        TimePerToken    = TimePerRun;
        RefTimePerToken = RefTimePerRun;
    } else { 
        TimePerToken    = TimePerRun     / double(TokenN);
        RefTimePerToken = RefTimePerRun  / double(TokenN);
    }
    // Clock Cycles per Token 
    CCT    = TimePerToken    / CycleTime;
    RefCCT = RefTimePerToken / CycleTime;

    cout << "//Result:\n";
    cout << "//   Time / Run:          " << (TimePerRun  - RefTimePerRun)  << endl;
    cout << "//   Time / Char:         " << (TimePerChar - RefTimePerChar) << endl;
    cout << "//   Clock Cycles / Char: " << (CCC - RefCCC)                 << endl;
    cout << "{" << endl;
    cout << "   generator       = {" << QUOTE_THIS(ANALYZER_GENERATOR) << "}," << endl;
#   if defined(ANALYZER_GENERATOR_FLEX)
#   else
    cout << "   quex_version    = {" << QUEX_VERSION << "}, " << endl;
#   endif
    cout << "   cpu_name        = {" << CPU_NAME << "}, " << endl;
    cout << "   cpu_code        = {" << CPU_CODE << "}, " << endl;
    cout << "   cpu_freq_mhz    = {" << CPU_FREQ_MHZ << "}, " << endl;
    cout << "   cc_name         = {" << CC_NAME << "}, " << endl;
    cout << "   cc_version      = {" << CC_VERSION << "}, " << endl;
    cout << "   cc_opt_flags    = {" << CC_OPTIMIZATION_FLAGS << "}, " << endl;
    cout << "   executable_size = {" << get_file_size(ThisExecutableName, true) << "}, " << endl;
    cout << "   os_name         = {" << OS_NAME << "}, " << endl;
    cout << "   tester_email    = {" << EMAIL << "}, " << endl;
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


double
report(const char* Name, double TimeDiff, double RepetitionN, size_t FileSize, size_t CharacterSize)
{ 
    using namespace std;

    const double  TimePerRun = TimeDiff / RepetitionN;

    printf("// Benchmark Results '%s'\n", Name);

    cout << "//    Total Time:  " << TimeDiff          << " [sec]" << endl;
    cout << "//    Runs:        " << (long)RepetitionN << " [1]"   << endl;
    cout << "//    TimePerRun:  " << TimePerRun        << " [sec]" << endl;

    const double  CharN          = FileSize / CHARACTER_SIZE;
    const double  CycleTime      = 1.0 / (CPU_FREQ_MHZ * 1e6);
    const double  TimePerChar    = TimePerRun  / CharN;
    const double  CCC            = TimePerChar / CycleTime;

    cout << "//    Time / Char:         " << TimePerChar << endl;
    cout << "//    Clock Cycles / Char: " << CCC         << endl;

    return TimePerRun;
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
