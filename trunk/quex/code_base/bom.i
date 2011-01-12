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
{| class="wikitable"
|-
! Encoding
! Representation ([[hexadecimal]])
! Representation ([[decimal]])
! Representation ([[ISO-8859-1]])
|-
| [[UTF-8]]
| <code>EF BB BF</code>{{#tag:ref|While identifying text as UTF-8, this is not really a "byte order" mark. Since the byte is also the word in UTF-8, there is no byte order to resolve.<ref name="utf-8-bom"/><ref>[http://tools.ietf.org/html/rfc3629#section-6 STD 63: UTF-8, a transformation of ISO 10646] Byte Order Mark (BOM)</ref>|group=t}}
| <code>239 187 191</code>
| <code>ï»¿</code>
|-
| [[UTF-16]] ([[Big Endian|BE]])
| <code>FE FF</code>
| <code>254 255</code>
| <code>þÿ</code>
|-
| [[UTF-16]] ([[Little Endian|LE]])
| <code>FF FE</code>
| <code>255 254</code>
| <code>ÿþ</code>
|-
| [[UTF-32]] (BE)
| <code>00 00 FE FF</code>
| <code>0 0 254 255</code>
| <code>□□þÿ</code> (□ is the ascii null character)
|-
| [[UTF-32]] (LE)
| <code>FF FE 00 00</code>
| <code>255 254 0 0</code>
| <code>ÿþ□□</code> (□ is the ascii null character)
|-
| [[UTF-7]]
| <code>2B 2F 76</code>, and ''one'' of the following: <code><nowiki>[ 38 | 39 | 2B | 2F ]</nowiki></code><ref group="t">In UTF-7, the fourth byte of the BOM, before encoding as [[base64]], is <code>001111xx</code> in binary, and <code>xx</code> depends on the next character (the first character after the BOM). Hence, technically, the fourth byte is not purely a part of the BOM, but also contains information about the next (non-BOM) character. For <code>xx=00</code>, <code>01</code>, <code>10</code>, <code>11</code>, this byte is, respectively, <code>38</code>, <code>39</code>, <code>2B</code>, or <code>2F</code> when encoded as base64. If no following character is encoded, <code>38</code> is used for the fourth byte and the following byte is <code>2D</code>.</ref>
| <code>43 47 118</code>, and ''one'' of the following: <code><nowiki>[ 56 | 57 | 43 | 47 ]</nowiki></code>
| <code>+/v</code>, and ''one'' of the following: <code><nowiki>8 9 + /</nowiki></code>
|-
| [[UTF-1]]
| <code>F7 64 4C</code>
| <code>247 100 76</code>
| <code>÷dL</code>
|-
| [[UTF-EBCDIC]]
| <code>DD 73 66 73</code>
| <code>221 115 102 115</code>
| <code>Ýsfs</code>
|-
| [[Standard Compression Scheme for Unicode|SCSU]]
| <code>0E FE FF</code>{{#tag:ref|SCSU allows other encodings of U+FEFF, the shown form is the signature recommended in UTR #6.<ref>[http://www.unicode.org/reports/tr6/#Signature UTR #6: Signature Byte Sequence for SCSU]</ref>|group=t}}
| <code>14 254 255</code>
| <code>□þÿ</code> (□ is the ascii "shift out" character)
|-
| [[BOCU-1]]
| <code>FB EE 28</code> ''optionally followed by'' <code>FF</code>{{#tag:ref|For BOCU-1 a signature changes the state of the decoder. Octet 0xFF resets the decoder to the initial state.<ref>[http://www.unicode.org/notes/tn6/#Signature UTN #6: Signature Byte Sequence]</ref>|group=t}}
| <code>251 238 40</code> ''optionally followed by'' <code>255</code>
| <code>ûî(</code> ''optionally followed by'' <code>ÿ</code>
|-
| [[GB-18030]]
| <code>84 31 95 33</code>
| <code>132 49 149 51</code>
| <code>□1■3</code> (□ and ■ are unmapped ISO-8859-1 characters)
|}
