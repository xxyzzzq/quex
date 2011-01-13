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


typedef enum {
    QUEX_BOM_NONE            = 0x000,
    QUEX_BOM_UTF_8           = 0x001,  /* D0 --> UTF 8       */
    QUEX_BOM_UTF_1           = 0x002,  /* D1 --> UTF 1       */
    QUEX_BOM_UTF_EBCDIC      = 0x004,  /* D2 --> UTF EBCDIC  */
    QUEX_BOM_BOCU_1          = 0x008,  /* D3 --> BOCU 1      */
    QUEX_BOM_GB_18030        = 0x010,  /* D4 --> GB_18030    */
    QUEX_BOM_UTF_7           = 0x020,  /* D5 --> UTF 7       */
    QUEX_BOM_UTF_16          = 0x040,  /* D6 --> UTF 16      */         
    QUEX_BOM_UTF_16_LE       = 0x041,
    QUEX_BOM_UTF_16_BE       = 0x042,  
    QUEX_BOM_UTF_32          = 0x080,  /* D7 --> UTF 32      */
    QUEX_BOM_UTF_32_LE       = 0x081,
    QUEX_BOM_UTF_32_BE       = 0x082,
    QUEX_BOM_SCSU            = 0x100,  /* D8 --> SCSU        */
    QUEX_BOM_SCSU_TO_UCS     = 0x101,  
    QUEX_BOM_SCSU_W0_TO_FE80 = 0x102, 
    QUEX_BOM_SCSU_W1_TO_FE80 = 0x103, 
    QUEX_BOM_SCSU_W2_TO_FE80 = 0x104, 
    QUEX_BOM_SCSU_W3_TO_FE80 = 0x105, 
    QUEX_BOM_SCSU_W4_TO_FE80 = 0x106, 
    QUEX_BOM_SCSU_W5_TO_FE80 = 0x107, 
    QUEX_BOM_SCSU_W6_TO_FE80 = 0x108, 
    QUEX_BOM_SCSU_W7_TO_FE80 = 0x109, 
} QUEX_TYPE_BOM;

/* Table of (known) BOMs _____________________________________________________
 *
 *         BOM_UTF_8        { 0xEF, 0xBB, 0xBF }
 *         UTF_16_BE        { 0xFE, 0xFF }
 *         UTF_16_LE        { 0xFF, 0xFE }
 *         UTF_32_BE        { 0x00, 0x00, 0xFE, 0xFF }
 *         UTF_32_LE        { 0xFF, 0xFE, 0x00, 0x00 }
 *         UTF_7_38         { 0x2B, 0x2F, 0x76, 0x38 }
 *         UTF_7_39         { 0x2B, 0x2F, 0x76, 0x39 }
 *         UTF_7_2B         { 0x2B, 0x2F, 0x76, 0x2B }
 *         UTF_7_2F         { 0x2B, 0x2F, 0x76, 0x2F }
 *         UTF_1            { 0xF7, 0x64, 0x4C }
 *         UTF_EBCDIC       { 0xDD, 0x73, 0x66, 0x73 }
 *         SCSU             { 0x0E, 0xFE, 0xFF }
 *         SCSU_TO_UCS      { 0x0F, 0xFE, 0xFF }
 *         SCSU_W0_TO_FE80  { 0x18, 0xA5, 0xFF }
 *         SCSU_W1_TO_FE80  { 0x19, 0xA5, 0xFF }
 *         SCSU_W2_TO_FE80  { 0x1A, 0xA5, 0xFF }
 *         SCSU_W3_TO_FE80  { 0x1B, 0xA5, 0xFF }
 *         SCSU_W4_TO_FE80  { 0x1C, 0xA5, 0xFF }
 *         SCSU_W5_TO_FE80  { 0x1D, 0xA5, 0xFF }
 *         SCSU_W6_TO_FE80  { 0x1E, 0xA5, 0xFF }
 *         SCSU_W7_TO_FE80  { 0x1F, 0xA5, 0xFF }
 *         BOCU_1_x         { 0xFB, 0xEE, 0x28, 0xFF }
 *         BOCU_1           { 0xFB, 0xEE, 0x28, }
 *         GB_18030         { 0x84, 0x31, 0x95, 0x33 }                         
 *_____________________________________________________________________________*/

QUEX_INLINE QUEX_TYPE_BOM
QUEX_NAME(bom_snap)(IH_TYPE InputHandle) 
{
    /* This function can **only** be used with **normally** behaving streams
     * where the position increases by one with every character being read. If
     * this is not the case then use the **binary** option of your stream.     */

    uint8_t        buffer[4] = { 0, 0, 0, 0};
    QUEX_TYPE_BOM  result    = QUEX_BOM_NONE;
    size_t         byte_n    = 0;

    p0     = QUEX_INPUT_POLICY_TELL(InputHandle, IH_TYPE);
    read_n = QUEX_INPUT_POLICY_LOAD_BYTES(InputHandle, IH_TYPE, buffer, 4) ) {
        return QUEX_BOM_NONE;
    }
    pEnd   = QUEX_INPUT_POLICY_TELL(InputHandle, IH_TYPE);

    /* For non-existing bytes fill 0x77, because it does not occur
     * anywhere as a criteria, see 'switch' after that.             */
    switch(read_n) {
        case 0: return QUEX_BOM_NONE;
        case 1: B1 = 0x77; B2 = 0x77; B3 = 0x77; break; 
        case 2:            B2 = 0x77; B3 = 0x77; break;
        case 3:                       B3 = 0x77; break;
    }

    result = QUEX_NAME(bom_identify)(buffer, &byte_n);
    QUEX_INPUT_POLICY_SEEK(InputHandle, IH_TYPE, p0 + byte_n);
    return result;
}

QUEX_INLINE QUEX_TYPE_BOM
QUEX_NAME(bom_identify)(uint8_t B0, uint8_t B1, uint8_t B2, uint8_t B3, size_t* n)
{

    x  = QUEX_BOM_NONE;

    switch( B0 ) {
    case 0x00: if( B1 == 0x00 && B2 == 0xFE && B3 == 0xFF ) { *n = 4; x = QUEX_BOM_UTF32_BE; }        break; 
    case 0x0E: if( B1 == 0xFE && B2 == 0xFF )               { *n = 3; x = QUEX_BOM_SCSU; }            break;
    case 0x0F: if( B1 == 0xFE && B2 == 0xFF )               { *n = 3; x = QUEX_BOM_SCSU_TO_UCS;       break; 
    case 0x18: if( B1 == 0xA5 && B2 == 0xFF )               { *n = 3; x = QUEX_BOM_SCSU_W0_TO_FE80; } break; 
    case 0x19: if( B1 == 0xA5 && B2 == 0xFF )               { *n = 3; x = QUEX_BOM_SCSU_W1_TO_FE80; } break; 
    case 0x1A: if( B1 == 0xA5 && B2 == 0xFF )               { *n = 3; x = QUEX_BOM_SCSU_W2_TO_FE80; } break; 
    case 0x1B: if( B1 == 0xA5 && B2 == 0xFF )               { *n = 3; x = QUEX_BOM_SCSU_W3_TO_FE80; } break; 
    case 0x1C: if( B1 == 0xA5 && B2 == 0xFF )               { *n = 3; x = QUEX_BOM_SCSU_W4_TO_FE80; } break; 
    case 0x1D: if( B1 == 0xA5 && B2 == 0xFF )               { *n = 3; x = QUEX_BOM_SCSU_W5_TO_FE80; } break; 
    case 0x1E: if( B1 == 0xA5 && B2 == 0xFF )               { *n = 3; x = QUEX_BOM_SCSU_W6_TO_FE80; } break; 
    case 0x1F: if( B1 == 0xA5 && B2 == 0xFF )               { *n = 3; x = QUEX_BOM_SCSU_W7_TO_FE80; } break; 
    case 0x2B: 
           /* In any case, the UTF7 BOM is not eaten. 
            * This is too complicated, since it uses a base64 code. It would require
            * to re-order the whole stream. This shall do the converter (if he wants). */
           *n = 0;
           if( B1 == 0x2F && B2 == 0x76 ) {
               switch( B3 ) 
               { case 0x2B: case 0x2F: case 0x38: case 0x39: x = QUEX_BOM_UTF7; } 
           }
           break;
    case 0x84: if( B1 == 0x31 && B2 == 0x95 && B3 == 0x33 ) { *n = 4; x = QUEX_BOM_GB_18030; }   break;
    case 0xDD: if( B1 == 0x73 && B2 == 0x66 && B3 == 0x73 ) { *n = 4; x = QUEX_BOM_UTF_EBCDIC; } break;
    case 0xEF: if( B1 == 0xBB && B2 == 0xBF )               { *n = 3; x = QUEX_BOM_BOM_UTF_8; }  break;
    case 0xF7: if( B1 == 0x64 && B2 == 0x4C )               { *n = 3; x = QUEX_BOM_UTF_1; }      break;
    case 0xFB: 
           if( B1 == 0xEE && B2 == 0x28 ) {
               if( B3 == 0xFF )  { *n = 4; x = QUEX_BOM_BOCU_1; } 
               else              { *n = 3; x = QUEX_BOM_BOCU_1; }
           }
           break;
    case 0xFE: 
           if( B1 == 0xFF )      { *n = 2; x = QUEX_BOM_UTF_16_BE; } break;
    case 0xFF: 
           if( B1 == 0xFE ) {
               else if( B2 == 0x00 && B3 == 0x00 ) { *n = 4; x = QUEX_BOM_UTF_32_LE; }
               else                                { *n = 2; x = QUEX_BOM_UTF_16_LE; } }
           }
           break;
    default: 
           *n = 0;
    }

    return x;
}           


#endif /* __QUEX_INCLUDE_GUARD__BOM_I */



















