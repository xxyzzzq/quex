/* -*- C++ -*- vim: set syntax=cpp:
 * 
 * ACKNOWLEDGEMENT: Parts of the following utf8 conversion have been derived from 
 *                  segments of the utf8 conversion library of Alexey Vatchenko 
 *                  <av@bsdua.org>.    
 *
 * (C) 2005-2009 Frank-Rene Schaefer                                                */

#ifndef __INCLUDE_GUARD_QUEX__CHARACTER_CONVERTER_cp737__
#define __INCLUDE_GUARD_QUEX__CHARACTER_CONVERTER_cp737__

#include <quex/code_base/definitions>
#include <quex/code_base/compatibility/inttypes.h>
#include <quex/code_base/asserts>

/* Converter Functions: ____________________________________________________________________
 *
 *   cp737_to_utf8(...)         -- character to utf8
 *   cp737_to_utf8_string(...)  -- string to utf8
 *   cp737_to_utf8_string(C++)  -- C++ string to utf8 (std::string)
 *
 *   cp737_to_wchar(...)        -- character to utf8
 *   cp737_to_wstring(...)      -- string to utf8
 *   cp737_to_wstring(C++)      -- C++ string to utf8 (std::wstring)
 *__________________________________________________________________________________________*/

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
QUEX_NAME(cp737_to_utf8)(const QUEX_TYPE_CHARACTER**  input_pp, 
                         uint8_t**                    output_pp)
{
    const int NEXT = 0x80;
    const int LEN2 = 0x0C0;
    const int LEN3 = 0x0E0;

    uint32_t   unicode  = 0xFFFF;
    uint8_t*   output_p = *output_pp;
    uint8_t*   p        = output_p;

    QUEX_TYPE_CHARACTER input = **input_pp;
    
    /* The unicode range simply does not go beyond 0x10FFFF */
    __quex_assert(input < 0x110000);
    /* If the following assert fails, then QUEX_TYPE_CHARACTER needs to be chosen
     * of 'unsigned' type, e.g. 'unsigned char' instead of 'char'.                */
    /* __quex_assert(input >= 0); */

#if 0
#   if defined(__QUEX_OPTION_LITTLE_ENDIAN)
#   define QUEX_BYTE_0  (*( ((uint8_t*)&unicode) + 3 ))
#   define QUEX_BYTE_1  (*( ((uint8_t*)&unicode) + 2 ))
#   define QUEX_BYTE_2  (*( ((uint8_t*)&unicode) + 1 ))
#   define QUEX_BYTE_3  (*( ((uint8_t*)&unicode) + 0 ))
#   else                             
#   define QUEX_BYTE_0  (*( ((uint8_t*)&unicode) + 0 ))
#   define QUEX_BYTE_1  (*( ((uint8_t*)&unicode) + 1 ))
#   define QUEX_BYTE_2  (*( ((uint8_t*)&unicode) + 2 ))
#   define QUEX_BYTE_3  (*( ((uint8_t*)&unicode) + 3 ))
#   endif
#else
#   define QUEX_BYTE_0  ((uint8_t)((unicode & 0xFF)))
#   define QUEX_BYTE_1  ((uint8_t)((unicode & 0xFF00) >> 8))
#   define QUEX_BYTE_2  ((uint8_t)((unicode & 0xFF0000) >> 16))
#   define QUEX_BYTE_3  ((uint8_t)((unicode & 0xFF000000) >> 24))
#endif

    if( input < 0x0000D3) {
        if( input < 0x0000BE) {
            if( input < 0x0000B4) {
                if( input < 0x0000A9) {
                    if( input < 0x000091) {
                        if( input < 0x000080) {
                            unicode = 0x000000 + (input - 0x000000);
                            *p = QUEX_BYTE_0; ++p;
                        } else {
                        
                            unicode = 0x000391 + (input - 0x000080);
                            *(p++) = LEN2 | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x07) << 2);
                            *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                        }
                    } else {
                    
                        if( input < 0x000098) {
                            unicode = 0x0003A3 + (input - 0x000091);
                        } else {
                        
                            unicode = 0x0003B1 + (input - 0x000098);
                        }
                        *(p++) = LEN2 | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x07) << 2);
                        *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                    }
                } else {
                
                    if( input < 0x0000AB) {
                        if( input < 0x0000AA) {
                            unicode = 0x0003C3 + (input - 0x0000A9);
                        } else {
                        
                            unicode = 0x0003C2 + (input - 0x0000AA);
                        }
                        *(p++) = LEN2 | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x07) << 2);
                        *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                    } else {
                    
                        if( input < 0x0000B0) {
                            unicode = 0x0003C4 + (input - 0x0000AB);
                            *(p++) = LEN2 | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x07) << 2);
                            *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                        } else {
                        
                            if( input < 0x0000B3) {
                                unicode = 0x002591 + (input - 0x0000B0);
                            } else {
                            
                                unicode = 0x002502 + (input - 0x0000B3);
                            }
                            *(p++) = LEN3 | ((QUEX_BYTE_1 & 0xf0) >> 4);
                            *(p++) = NEXT | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x0f) << 2);
                            *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                        }
                    }
                }
            } else {
            
                if( input < 0x0000B9) {
                    if( input < 0x0000B7) {
                        if( input < 0x0000B5) {
                            unicode = 0x002524 + (input - 0x0000B4);
                        } else {
                        
                            unicode = 0x002561 + (input - 0x0000B5);
                        }
                    } else {
                    
                        if( input < 0x0000B8) {
                            unicode = 0x002556 + (input - 0x0000B7);
                        } else {
                        
                            unicode = 0x002555 + (input - 0x0000B8);
                        }
                    }
                } else {
                
                    if( input < 0x0000BB) {
                        if( input < 0x0000BA) {
                            unicode = 0x002563 + (input - 0x0000B9);
                        } else {
                        
                            unicode = 0x002551 + (input - 0x0000BA);
                        }
                    } else {
                    
                        if( input < 0x0000BC) {
                            unicode = 0x002557 + (input - 0x0000BB);
                        } else {
                        
                            if( input < 0x0000BD) {
                                unicode = 0x00255D + (input - 0x0000BC);
                            } else {
                            
                                unicode = 0x00255C + (input - 0x0000BD);
                            }
                        }
                    }
                }
                *(p++) = LEN3 | ((QUEX_BYTE_1 & 0xf0) >> 4);
                *(p++) = NEXT | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x0f) << 2);
                *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
            }
        } else {
        
            if( input < 0x0000C8) {
                if( input < 0x0000C2) {
                    if( input < 0x0000C0) {
                        if( input < 0x0000BF) {
                            unicode = 0x00255B + (input - 0x0000BE);
                        } else {
                        
                            unicode = 0x002510 + (input - 0x0000BF);
                        }
                    } else {
                    
                        if( input < 0x0000C1) {
                            unicode = 0x002514 + (input - 0x0000C0);
                        } else {
                        
                            unicode = 0x002534 + (input - 0x0000C1);
                        }
                    }
                } else {
                
                    if( input < 0x0000C4) {
                        if( input < 0x0000C3) {
                            unicode = 0x00252C + (input - 0x0000C2);
                        } else {
                        
                            unicode = 0x00251C + (input - 0x0000C3);
                        }
                    } else {
                    
                        if( input < 0x0000C5) {
                            unicode = 0x002500 + (input - 0x0000C4);
                        } else {
                        
                            if( input < 0x0000C6) {
                                unicode = 0x00253C + (input - 0x0000C5);
                            } else {
                            
                                unicode = 0x00255E + (input - 0x0000C6);
                            }
                        }
                    }
                }
            } else {
            
                if( input < 0x0000CC) {
                    if( input < 0x0000CA) {
                        if( input < 0x0000C9) {
                            unicode = 0x00255A + (input - 0x0000C8);
                        } else {
                        
                            unicode = 0x002554 + (input - 0x0000C9);
                        }
                    } else {
                    
                        if( input < 0x0000CB) {
                            unicode = 0x002569 + (input - 0x0000CA);
                        } else {
                        
                            unicode = 0x002566 + (input - 0x0000CB);
                        }
                    }
                } else {
                
                    if( input < 0x0000CE) {
                        if( input < 0x0000CD) {
                            unicode = 0x002560 + (input - 0x0000CC);
                        } else {
                        
                            unicode = 0x002550 + (input - 0x0000CD);
                        }
                    } else {
                    
                        if( input < 0x0000CF) {
                            unicode = 0x00256C + (input - 0x0000CE);
                        } else {
                        
                            if( input < 0x0000D1) {
                                unicode = 0x002567 + (input - 0x0000CF);
                            } else {
                            
                                unicode = 0x002564 + (input - 0x0000D1);
                            }
                        }
                    }
                }
            }
            *(p++) = LEN3 | ((QUEX_BYTE_1 & 0xf0) >> 4);
            *(p++) = NEXT | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x0f) << 2);
            *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
        }
    } else {
    
        if( input < 0x0000E9) {
            if( input < 0x0000DD) {
                if( input < 0x0000D8) {
                    if( input < 0x0000D5) {
                        if( input < 0x0000D4) {
                            unicode = 0x002559 + (input - 0x0000D3);
                        } else {
                        
                            unicode = 0x002558 + (input - 0x0000D4);
                        }
                    } else {
                    
                        if( input < 0x0000D7) {
                            unicode = 0x002552 + (input - 0x0000D5);
                        } else {
                        
                            unicode = 0x00256B + (input - 0x0000D7);
                        }
                    }
                } else {
                
                    if( input < 0x0000DA) {
                        if( input < 0x0000D9) {
                            unicode = 0x00256A + (input - 0x0000D8);
                        } else {
                        
                            unicode = 0x002518 + (input - 0x0000D9);
                        }
                    } else {
                    
                        if( input < 0x0000DB) {
                            unicode = 0x00250C + (input - 0x0000DA);
                        } else {
                        
                            if( input < 0x0000DC) {
                                unicode = 0x002588 + (input - 0x0000DB);
                            } else {
                            
                                unicode = 0x002584 + (input - 0x0000DC);
                            }
                        }
                    }
                }
                *(p++) = LEN3 | ((QUEX_BYTE_1 & 0xf0) >> 4);
                *(p++) = NEXT | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x0f) << 2);
                *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
            } else {
            
                if( input < 0x0000E1) {
                    if( input < 0x0000DF) {
                        if( input < 0x0000DE) {
                            unicode = 0x00258C + (input - 0x0000DD);
                        } else {
                        
                            unicode = 0x002590 + (input - 0x0000DE);
                        }
                        *(p++) = LEN3 | ((QUEX_BYTE_1 & 0xf0) >> 4);
                        *(p++) = NEXT | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x0f) << 2);
                        *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                    } else {
                    
                        if( input < 0x0000E0) {
                            unicode = 0x002580 + (input - 0x0000DF);
                            *(p++) = LEN3 | ((QUEX_BYTE_1 & 0xf0) >> 4);
                            *(p++) = NEXT | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x0f) << 2);
                            *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                        } else {
                        
                            unicode = 0x0003C9 + (input - 0x0000E0);
                            *(p++) = LEN2 | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x07) << 2);
                            *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                        }
                    }
                } else {
                
                    if( input < 0x0000E5) {
                        if( input < 0x0000E4) {
                            unicode = 0x0003AC + (input - 0x0000E1);
                        } else {
                        
                            unicode = 0x0003CA + (input - 0x0000E4);
                        }
                    } else {
                    
                        if( input < 0x0000E6) {
                            unicode = 0x0003AF + (input - 0x0000E5);
                        } else {
                        
                            if( input < 0x0000E8) {
                                unicode = 0x0003CC + (input - 0x0000E6);
                            } else {
                            
                                unicode = 0x0003CB + (input - 0x0000E8);
                            }
                        }
                    }
                    *(p++) = LEN2 | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x07) << 2);
                    *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                }
            }
        } else {
        
            if( input < 0x0000F6) {
                if( input < 0x0000EF) {
                    if( input < 0x0000EB) {
                        if( input < 0x0000EA) {
                            unicode = 0x0003CE + (input - 0x0000E9);
                        } else {
                        
                            unicode = 0x000386 + (input - 0x0000EA);
                        }
                    } else {
                    
                        if( input < 0x0000EE) {
                            unicode = 0x000388 + (input - 0x0000EB);
                        } else {
                        
                            unicode = 0x00038C + (input - 0x0000EE);
                        }
                    }
                    *(p++) = LEN2 | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x07) << 2);
                    *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                } else {
                
                    if( input < 0x0000F2) {
                        if( input < 0x0000F1) {
                            unicode = 0x00038E + (input - 0x0000EF);
                        } else {
                        
                            unicode = 0x0000B1 + (input - 0x0000F1);
                        }
                        *(p++) = LEN2 | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x07) << 2);
                        *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                    } else {
                    
                        if( input < 0x0000F3) {
                            unicode = 0x002265 + (input - 0x0000F2);
                            *(p++) = LEN3 | ((QUEX_BYTE_1 & 0xf0) >> 4);
                            *(p++) = NEXT | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x0f) << 2);
                            *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                        } else {
                        
                            if( input < 0x0000F4) {
                                unicode = 0x002264 + (input - 0x0000F3);
                                *(p++) = LEN3 | ((QUEX_BYTE_1 & 0xf0) >> 4);
                                *(p++) = NEXT | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x0f) << 2);
                                *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                            } else {
                            
                                unicode = 0x0003AA + (input - 0x0000F4);
                                *(p++) = LEN2 | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x07) << 2);
                                *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                            }
                        }
                    }
                }
            } else {
            
                if( input < 0x0000FB) {
                    if( input < 0x0000F8) {
                        if( input < 0x0000F7) {
                            unicode = 0x0000F7 + (input - 0x0000F6);
                            *(p++) = LEN2 | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x07) << 2);
                            *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                        } else {
                        
                            unicode = 0x002248 + (input - 0x0000F7);
                            *(p++) = LEN3 | ((QUEX_BYTE_1 & 0xf0) >> 4);
                            *(p++) = NEXT | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x0f) << 2);
                            *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                        }
                    } else {
                    
                        if( input < 0x0000F9) {
                            unicode = 0x0000B0 + (input - 0x0000F8);
                            *(p++) = LEN2 | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x07) << 2);
                            *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                        } else {
                        
                            if( input < 0x0000FA) {
                                unicode = 0x002219 + (input - 0x0000F9);
                                *(p++) = LEN3 | ((QUEX_BYTE_1 & 0xf0) >> 4);
                                *(p++) = NEXT | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x0f) << 2);
                                *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                            } else {
                            
                                unicode = 0x0000B7 + (input - 0x0000FA);
                                *(p++) = LEN2 | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x07) << 2);
                                *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                            }
                        }
                    }
                } else {
                
                    if( input < 0x0000FD) {
                        if( input < 0x0000FC) {
                            unicode = 0x00221A + (input - 0x0000FB);
                        } else {
                        
                            unicode = 0x00207F + (input - 0x0000FC);
                        }
                        *(p++) = LEN3 | ((QUEX_BYTE_1 & 0xf0) >> 4);
                        *(p++) = NEXT | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x0f) << 2);
                        *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                    } else {
                    
                        if( input < 0x0000FE) {
                            unicode = 0x0000B2 + (input - 0x0000FD);
                            *(p++) = LEN2 | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x07) << 2);
                            *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                        } else {
                        
                            if( input < 0x0000FF) {
                                unicode = 0x0025A0 + (input - 0x0000FE);
                                *(p++) = LEN3 | ((QUEX_BYTE_1 & 0xf0) >> 4);
                                *(p++) = NEXT | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x0f) << 2);
                                *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                            } else {
                            
                                unicode = 0x0000A0 + (input - 0x0000FF);
                                *(p++) = LEN2 | (QUEX_BYTE_0 >> 6) | ((QUEX_BYTE_1 & 0x07) << 2);
                                *(p++) = NEXT | (QUEX_BYTE_0 & 0x3f);
                            }
                        }
                    }
                }
            }
        }
    }

    __quex_assert(p - output_p < (ptrdiff_t)7);
    __quex_assert(p > output_p);
    *output_pp = p;
    ++(*input_pp);

#   undef QUEX_BYTE_0 
#   undef QUEX_BYTE_1 
#   undef QUEX_BYTE_2 
#   undef QUEX_BYTE_3 
}

QUEX_INLINE void
QUEX_NAME(cp737_to_utf8_string)(const QUEX_TYPE_CHARACTER**  source_pp, 
                                    const QUEX_TYPE_CHARACTER*   SourceEnd, 
                                    uint8_t**                    drain_pp,  
                                    uint8_t*                     DrainEnd)
{
    const QUEX_TYPE_CHARACTER*  source_iterator; 
    uint8_t*                    drain_iterator;

    __quex_assert(source_pp != 0x0);
    __quex_assert(*source_pp != 0x0);
    __quex_assert(drain_pp != 0x0);
    __quex_assert(*drain_pp != 0x0);

    drain_iterator  = *drain_pp;
    source_iterator = *source_pp;

    while( 1 + 1 == 2 ) { 
        if( source_iterator == SourceEnd ) break;
        if( DrainEnd - drain_iterator < (ptrdiff_t)5 ) break;
        QUEX_NAME(cp737_to_utf8)(&source_iterator, &drain_iterator);
    }

    *drain_pp  = drain_iterator;
    *source_pp = source_iterator;
}

#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::string
QUEX_NAME(cp737_to_utf8_string)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source)
{
    const QUEX_TYPE_CHARACTER*  source_iterator = (QUEX_TYPE_CHARACTER*)Source.c_str();
    const QUEX_TYPE_CHARACTER*  source_end      = source_iterator + Source.length();
    uint8_t                     drain[8];
    uint8_t*                    drain_iterator = 0;
    std::string                 result;

    for(; source_iterator != source_end; ++source_iterator) {
        drain_iterator = drain;
        QUEX_NAME(cp737_to_utf8)(&source_iterator, &drain_iterator);
        result.append((char*)drain, (drain_iterator - drain));
    }
    return result;
}

#if ! defined(__QUEX_OPTION_WCHAR_T_DISABLED)

QUEX_INLINE void
QUEX_NAME(cp737_to_wchar)(const QUEX_TYPE_CHARACTER** input_pp,
                              __QUEX_STD_wchar_t**        output_pp)
{
    uint32_t             unicode = 0L;
    QUEX_TYPE_CHARACTER  input = **input_pp;
    if( input < 0x0000D3) {
        if( input < 0x0000BE) {
            if( input < 0x0000B4) {
                if( input < 0x0000A9) {
                    if( input < 0x000091) {
                        if( input < 0x000080) {
                            unicode = 0x000000 + (input - 0x000000);
                        } else {
                        
                            unicode = 0x000391 + (input - 0x000080);
                        }
                    } else {
                    
                        if( input < 0x000098) {
                            unicode = 0x0003A3 + (input - 0x000091);
                        } else {
                        
                            unicode = 0x0003B1 + (input - 0x000098);
                        }
                    }
                } else {
                
                    if( input < 0x0000AB) {
                        if( input < 0x0000AA) {
                            unicode = 0x0003C3 + (input - 0x0000A9);
                        } else {
                        
                            unicode = 0x0003C2 + (input - 0x0000AA);
                        }
                    } else {
                    
                        if( input < 0x0000B0) {
                            unicode = 0x0003C4 + (input - 0x0000AB);
                        } else {
                        
                            if( input < 0x0000B3) {
                                unicode = 0x002591 + (input - 0x0000B0);
                            } else {
                            
                                unicode = 0x002502 + (input - 0x0000B3);
                            }
                        }
                    }
                }
            } else {
            
                if( input < 0x0000B9) {
                    if( input < 0x0000B7) {
                        if( input < 0x0000B5) {
                            unicode = 0x002524 + (input - 0x0000B4);
                        } else {
                        
                            unicode = 0x002561 + (input - 0x0000B5);
                        }
                    } else {
                    
                        if( input < 0x0000B8) {
                            unicode = 0x002556 + (input - 0x0000B7);
                        } else {
                        
                            unicode = 0x002555 + (input - 0x0000B8);
                        }
                    }
                } else {
                
                    if( input < 0x0000BB) {
                        if( input < 0x0000BA) {
                            unicode = 0x002563 + (input - 0x0000B9);
                        } else {
                        
                            unicode = 0x002551 + (input - 0x0000BA);
                        }
                    } else {
                    
                        if( input < 0x0000BC) {
                            unicode = 0x002557 + (input - 0x0000BB);
                        } else {
                        
                            if( input < 0x0000BD) {
                                unicode = 0x00255D + (input - 0x0000BC);
                            } else {
                            
                                unicode = 0x00255C + (input - 0x0000BD);
                            }
                        }
                    }
                }
            }
        } else {
        
            if( input < 0x0000C8) {
                if( input < 0x0000C2) {
                    if( input < 0x0000C0) {
                        if( input < 0x0000BF) {
                            unicode = 0x00255B + (input - 0x0000BE);
                        } else {
                        
                            unicode = 0x002510 + (input - 0x0000BF);
                        }
                    } else {
                    
                        if( input < 0x0000C1) {
                            unicode = 0x002514 + (input - 0x0000C0);
                        } else {
                        
                            unicode = 0x002534 + (input - 0x0000C1);
                        }
                    }
                } else {
                
                    if( input < 0x0000C4) {
                        if( input < 0x0000C3) {
                            unicode = 0x00252C + (input - 0x0000C2);
                        } else {
                        
                            unicode = 0x00251C + (input - 0x0000C3);
                        }
                    } else {
                    
                        if( input < 0x0000C5) {
                            unicode = 0x002500 + (input - 0x0000C4);
                        } else {
                        
                            if( input < 0x0000C6) {
                                unicode = 0x00253C + (input - 0x0000C5);
                            } else {
                            
                                unicode = 0x00255E + (input - 0x0000C6);
                            }
                        }
                    }
                }
            } else {
            
                if( input < 0x0000CC) {
                    if( input < 0x0000CA) {
                        if( input < 0x0000C9) {
                            unicode = 0x00255A + (input - 0x0000C8);
                        } else {
                        
                            unicode = 0x002554 + (input - 0x0000C9);
                        }
                    } else {
                    
                        if( input < 0x0000CB) {
                            unicode = 0x002569 + (input - 0x0000CA);
                        } else {
                        
                            unicode = 0x002566 + (input - 0x0000CB);
                        }
                    }
                } else {
                
                    if( input < 0x0000CE) {
                        if( input < 0x0000CD) {
                            unicode = 0x002560 + (input - 0x0000CC);
                        } else {
                        
                            unicode = 0x002550 + (input - 0x0000CD);
                        }
                    } else {
                    
                        if( input < 0x0000CF) {
                            unicode = 0x00256C + (input - 0x0000CE);
                        } else {
                        
                            if( input < 0x0000D1) {
                                unicode = 0x002567 + (input - 0x0000CF);
                            } else {
                            
                                unicode = 0x002564 + (input - 0x0000D1);
                            }
                        }
                    }
                }
            }
        }
    } else {
    
        if( input < 0x0000E9) {
            if( input < 0x0000DD) {
                if( input < 0x0000D8) {
                    if( input < 0x0000D5) {
                        if( input < 0x0000D4) {
                            unicode = 0x002559 + (input - 0x0000D3);
                        } else {
                        
                            unicode = 0x002558 + (input - 0x0000D4);
                        }
                    } else {
                    
                        if( input < 0x0000D7) {
                            unicode = 0x002552 + (input - 0x0000D5);
                        } else {
                        
                            unicode = 0x00256B + (input - 0x0000D7);
                        }
                    }
                } else {
                
                    if( input < 0x0000DA) {
                        if( input < 0x0000D9) {
                            unicode = 0x00256A + (input - 0x0000D8);
                        } else {
                        
                            unicode = 0x002518 + (input - 0x0000D9);
                        }
                    } else {
                    
                        if( input < 0x0000DB) {
                            unicode = 0x00250C + (input - 0x0000DA);
                        } else {
                        
                            if( input < 0x0000DC) {
                                unicode = 0x002588 + (input - 0x0000DB);
                            } else {
                            
                                unicode = 0x002584 + (input - 0x0000DC);
                            }
                        }
                    }
                }
            } else {
            
                if( input < 0x0000E1) {
                    if( input < 0x0000DF) {
                        if( input < 0x0000DE) {
                            unicode = 0x00258C + (input - 0x0000DD);
                        } else {
                        
                            unicode = 0x002590 + (input - 0x0000DE);
                        }
                    } else {
                    
                        if( input < 0x0000E0) {
                            unicode = 0x002580 + (input - 0x0000DF);
                        } else {
                        
                            unicode = 0x0003C9 + (input - 0x0000E0);
                        }
                    }
                } else {
                
                    if( input < 0x0000E5) {
                        if( input < 0x0000E4) {
                            unicode = 0x0003AC + (input - 0x0000E1);
                        } else {
                        
                            unicode = 0x0003CA + (input - 0x0000E4);
                        }
                    } else {
                    
                        if( input < 0x0000E6) {
                            unicode = 0x0003AF + (input - 0x0000E5);
                        } else {
                        
                            if( input < 0x0000E8) {
                                unicode = 0x0003CC + (input - 0x0000E6);
                            } else {
                            
                                unicode = 0x0003CB + (input - 0x0000E8);
                            }
                        }
                    }
                }
            }
        } else {
        
            if( input < 0x0000F6) {
                if( input < 0x0000EF) {
                    if( input < 0x0000EB) {
                        if( input < 0x0000EA) {
                            unicode = 0x0003CE + (input - 0x0000E9);
                        } else {
                        
                            unicode = 0x000386 + (input - 0x0000EA);
                        }
                    } else {
                    
                        if( input < 0x0000EE) {
                            unicode = 0x000388 + (input - 0x0000EB);
                        } else {
                        
                            unicode = 0x00038C + (input - 0x0000EE);
                        }
                    }
                } else {
                
                    if( input < 0x0000F2) {
                        if( input < 0x0000F1) {
                            unicode = 0x00038E + (input - 0x0000EF);
                        } else {
                        
                            unicode = 0x0000B1 + (input - 0x0000F1);
                        }
                    } else {
                    
                        if( input < 0x0000F3) {
                            unicode = 0x002265 + (input - 0x0000F2);
                        } else {
                        
                            if( input < 0x0000F4) {
                                unicode = 0x002264 + (input - 0x0000F3);
                            } else {
                            
                                unicode = 0x0003AA + (input - 0x0000F4);
                            }
                        }
                    }
                }
            } else {
            
                if( input < 0x0000FB) {
                    if( input < 0x0000F8) {
                        if( input < 0x0000F7) {
                            unicode = 0x0000F7 + (input - 0x0000F6);
                        } else {
                        
                            unicode = 0x002248 + (input - 0x0000F7);
                        }
                    } else {
                    
                        if( input < 0x0000F9) {
                            unicode = 0x0000B0 + (input - 0x0000F8);
                        } else {
                        
                            if( input < 0x0000FA) {
                                unicode = 0x002219 + (input - 0x0000F9);
                            } else {
                            
                                unicode = 0x0000B7 + (input - 0x0000FA);
                            }
                        }
                    }
                } else {
                
                    if( input < 0x0000FD) {
                        if( input < 0x0000FC) {
                            unicode = 0x00221A + (input - 0x0000FB);
                        } else {
                        
                            unicode = 0x00207F + (input - 0x0000FC);
                        }
                    } else {
                    
                        if( input < 0x0000FE) {
                            unicode = 0x0000B2 + (input - 0x0000FD);
                        } else {
                        
                            if( input < 0x0000FF) {
                                unicode = 0x0025A0 + (input - 0x0000FE);
                            } else {
                            
                                unicode = 0x0000A0 + (input - 0x0000FF);
                            }
                        }
                    }
                }
            }
        }
    }
    return unicode;

    ++(*input_pp);
    ++(*output_pp);
}

QUEX_INLINE void
QUEX_NAME(cp737_to_wstring)(const QUEX_TYPE_CHARACTER**  source_pp, 
                                const QUEX_TYPE_CHARACTER*   SourceEnd, 
                                uint8_t**                    drain_pp,  
                                uint8_t*                     DrainEnd)
{
    const QUEX_TYPE_CHARACTER*  source_iterator; 
    uint8_t*                    drain_iterator;

    __quex_assert(source_pp != 0x0);
    __quex_assert(*source_pp != 0x0);
    __quex_assert(drain_pp != 0x0);
    __quex_assert(*drain_pp != 0x0);

    drain_iterator  = *drain_pp;
    source_iterator = *source_pp;

    while( 1 + 1 == 2 ) { 
        if( source_iterator == SourceEnd ) break;
        if( drain_iterator == DrainEnd ) break;
        QUEX_NAME(cp737_to_utf8)(&source_iterator, &drain_iterator);
    }

    *drain_pp  = drain_iterator;
    *source_pp = source_iterator;
}


#if ! defined(__QUEX_OPTION_PLAIN_C)
QUEX_INLINE std::wstring
QUEX_NAME(cp737_to_wstring)(const std::basic_string<QUEX_TYPE_CHARACTER>& Source)
{
    const QUEX_TYPE_CHARACTER*   source_iterator = (QUEX_TYPE_CHARACTER*)Source.c_str();
    const QUEX_TYPE_CHARACTER*   source_end      = source_iterator + Source.length();
    __QUEX_STD_wchar_t           drain[1];
    __QUEX_STD_wchar_t*          drain_iterator = 0x0;
    std::wstring                 result;

    for(; source_iterator != source_end; ++source_iterator) {
        drain_iterator = (__QUEX_STD_wchar_t*)drain;
        QUEX_NAME(cp737_to_wchar)(&source_iterator, &drain_iterator);
        result.push_back(drain[0]);
    }
    return result;
}
#endif

#endif

#endif /* __QUEX_OPTION_PLAIN_C */

QUEX_NAMESPACE_MAIN_CLOSE

#endif /* __INCLUDE_GUARD_QUEX__CHARACTER_CONVERTER_cp737__ */

