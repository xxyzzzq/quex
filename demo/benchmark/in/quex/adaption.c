#include <in/main.h>

quex::quex_scan*  global_qlex; 
quex::Token       global_token; 

void scan_init(size_t FileSize)
{
    global_qlex = new quex::quex_scan(global_fh);
#   ifdef QUEX_OPTION_TOKEN_POLICY_USERS_TOKEN
    global_qlex->token = &global_token;
#   endif
}
