/* -*- C++ -*- vim:set syntax=cpp: 
 *
 * Byte Order Mark (BOM) Handling.
 *
 * The byte order mark (BOM) is a Unicode character used to signal 
 * the endianness (byte order) of a text file or stream. Its code 
 * point is U+FEFF. 
 * [Source: <http://en.wikipedia.org/wiki/Byte_order_mark>]
 *
 * This file implements a function to cut the BOM and tell about 
 * the encoding of the data stream.
 *
 * (C) 2010 Frank-Rene Schaefer    
 * ABSOLUTELY NO WARRANTY                    */
#ifndef __QUEX_INCLUDE_GUARD__BOM_I
#define __QUEX_INCLUDE_GUARD__BOM_I


#endif /* __QUEX_INCLUDE_GUARD__AUX_STRING_I */

typedef enum {
    QUEX_BOM_UTF_8           = 0x00,  /* First Nibble  */
    QUEX_BOM_UTF_1           = 0x01,  
    QUEX_BOM_UTF_EBCDIC      = 0x02,
    QUEX_BOM_BOCU_1          = 0x03,
    QUEX_BOM_GB_18030        = 0x04,
    QUEX_BOM_UTF_16          = 0x10,  /* D4 --> UTF 16 */         
    QUEX_BOM_UTF_16_LE       = 0x11,
    QUEX_BOM_UTF_16_BE       = 0x12,  
    QUEX_BOM_UTF_32          = 0x20,  /* D5 --> UTF 32 */
    QUEX_BOM_UTF_32_LE       = 0x21,
    QUEX_BOM_UTF_32_BE       = 0x22,
    QUEX_BOM_UTF_7           = 0x40,  /* D6 --> UTF 7  */
    QUEX_BOM_UTF_7_38        = 0x41,   
    QUEX_BOM_UTF_7_39        = 0x42,
    QUEX_BOM_UTF_7_2B        = 0x43, 
    QUEX_BOM_UTF_7_2F        = 0x44, 
    QUEX_BOM_SCSU            = 0x80,  /* D7 --> SCSU   */
    QUEX_BOM_SCSU_TO_UCS     = 0x81,  
    QUEX_BOM_SCSU_W0_TO_FE80 = 0x81, 
    QUEX_BOM_SCSU_W1_TO_FE80 = 0x81, 
    QUEX_BOM_SCSU_W2_TO_FE80 = 0x81, 
    QUEX_BOM_SCSU_W3_TO_FE80 = 0x81, 
    QUEX_BOM_SCSU_W4_TO_FE80 = 0x81, 
    QUEX_BOM_SCSU_W5_TO_FE80 = 0x81, 
    QUEX_BOM_SCSU_W6_TO_FE80 = 0x81, 
    QUEX_BOM_SCSU_W7_TO_FE80 = 0x81, 
} QUEX_TYPE_BOM;

const uint8_t BOM_UTF_8       = { 0xEF, 0xBB, 0xBF };
const uint8_t UTF_16_BE       = { 0xFE, 0xFF };
const uint8_t UTF_16_LE       = { 0xFF, 0xFE };
const uint8_t UTF_32_BE       = { 0x00, 0x00, 0xFE, 0xFF };
const uint8_t UTF_32_LE       = { 0xFF, 0xFE, 0x00, 0x00 };
const uint8_t UTF_7_38        = { 0x2B, 0x2F, 0x76, 0x38 };
const uint8_t UTF_7_39        = { 0x2B, 0x2F, 0x76, 0x39 };
const uint8_t UTF_7_2B        = { 0x2B, 0x2F, 0x76, 0x2B };
const uint8_t UTF_7_2F        = { 0x2B, 0x2F, 0x76, 0x2F };
const uint8_t UTF_1           = { 0xF7, 0x64, 0x4C };
const uint8_t UTF_EBCDIC      = { 0xDD, 0x73, 0x66, 0x73 };
const uint8_t SCSU            = { 0x0E, 0xFE, 0xFF };
const uint8_t SCSU_TO_UCS     = { 0x0F, 0xFE, 0xFF };
const uint8_t SCSU_W0_TO_FE80 = { 0x18, 0xA5, 0xFF };
const uint8_t SCSU_W1_TO_FE80 = { 0x19, 0xA5, 0xFF };
const uint8_t SCSU_W2_TO_FE80 = { 0x1A, 0xA5, 0xFF };
const uint8_t SCSU_W3_TO_FE80 = { 0x1B, 0xA5, 0xFF };
const uint8_t SCSU_W4_TO_FE80 = { 0x1C, 0xA5, 0xFF };
const uint8_t SCSU_W5_TO_FE80 = { 0x1D, 0xA5, 0xFF };
const uint8_t SCSU_W6_TO_FE80 = { 0x1E, 0xA5, 0xFF };
const uint8_t SCSU_W7_TO_FE80 = { 0x1F, 0xA5, 0xFF };
const uint8_t BOCU_1_x        = { 0xFB, 0xEE, 0x28, 0xFF };
const uint8_t BOCU_1          = { 0xFB, 0xEE, 0x28, };
const uint8_t GB_18030        = { 0x84, 0x31, 0x95, 0x33 };



case 0x00: 0x00, 0xFE, 0xFF };  const uint8_t UTF_32_BE       = { 
case 0x0E: 0xFE, 0xFF };        const uint8_t SCSU            = { 
case 0x0F: 0xFE, 0xFF };        const uint8_t SCSU_TO_UCS     = { 
case 0x18: 0xA5, 0xFF };        const uint8_t SCSU_W0_TO_FE80 = { 
case 0x19: 0xA5, 0xFF };        const uint8_t SCSU_W1_TO_FE80 = { 
case 0x1A: 0xA5, 0xFF };        const uint8_t SCSU_W2_TO_FE80 = { 
case 0x1B: 0xA5, 0xFF };        const uint8_t SCSU_W3_TO_FE80 = { 
case 0x1C: 0xA5, 0xFF };        const uint8_t SCSU_W4_TO_FE80 = { 
case 0x1D: 0xA5, 0xFF };        const uint8_t SCSU_W5_TO_FE80 = { 
case 0x1E: 0xA5, 0xFF };        const uint8_t SCSU_W6_TO_FE80 = { 
case 0x1F: 0xA5, 0xFF };        const uint8_t SCSU_W7_TO_FE80 = { 
case 0x2B: 0x2F, 0x76, 0x2B };  const uint8_t UTF_7_2B        = { 
           0x2F, 0x76, 0x2F };  const uint8_t UTF_7_2F        = { 
           0x2F, 0x76, 0x38 };  const uint8_t UTF_7_38        = { 
           0x2F, 0x76, 0x39 };  const uint8_t UTF_7_39        = { 
case 0x84: 0x31, 0x95, 0x33 };  const uint8_t GB_18030        = { 
case 0xDD: 0x73, 0x66, 0x73 };  const uint8_t UTF_EBCDIC      = { 
case 0xEF: 0xBB, 0xBF };        const uint8_t BOM_UTF_8       = { 
case 0xF7: 0x64, 0x4C };        const uint8_t UTF_1           = { 
case 0xFB: 0xEE, 0x28, 0xFF };  const uint8_t BOCU_1_x        = { 
           0xEE, 0x28, };       const uint8_t BOCU_1          = { 
case 0xFE: 0xFF };              const uint8_t UTF_16_BE       = { 
case 0xFF: 0xFE };              const uint8_t UTF_16_LE       = { 
           0xFE, 0x00, 0x00 };  const uint8_t UTF_32_LE       = { 




















