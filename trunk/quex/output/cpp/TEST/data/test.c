#include <data/check.h>

#ifdef __QUEX_OPTION_COUNTER
void
QUEX_NAME(TEST_MODE_counter)(QUEX_TYPE_ANALYZER* me, const QUEX_TYPE_CHARACTER* LexemeBegin, const QUEX_TYPE_CHARACTER* LexemeEnd)
{
#   define self (*me)
    const QUEX_TYPE_CHARACTER* iterator    = (const QUEX_TYPE_CHARACTER*)0;
    QUEX_TYPE_CHARACTER        input       = (QUEX_TYPE_CHARACTER)0;
    __QUEX_IF_COUNT_SHIFT_VALUES();

    __quex_assert(LexemeBegin <= LexemeEnd);
    for(iterator=LexemeBegin; iterator < LexemeEnd; ) {
    input = *iterator;
    __quex_debug("Init State\n");
    __quex_debug_state(288);
    if( input < 0xE0 ) {
        if( input < 0x80 ) {
            if( input >= 0xE ) {
                goto _294;
            } else if( input == 0xD ) {
                goto _301;
            } else if( input >= 0xA ) {
                goto _303;
            } else if( input == 0x9 ) {
                goto _290;
            } else {
                goto _294;
            }
        } else {
            switch( input ) {
                case 0xC2: goto _296;
                case 0xC3: 
                case 0xC4: 
                case 0xC5: 
                case 0xC6: 
                case 0xC7: 
                case 0xC8: 
                case 0xC9: 
                case 0xCA: 
                case 0xCB: 
                case 0xCC: 
                case 0xCD: 
                case 0xCE: 
                case 0xCF: 
                case 0xD0: 
                case 0xD1: 
                case 0xD2: 
                case 0xD3: 
                case 0xD4: 
                case 0xD5: 
                case 0xD6: 
                case 0xD7: goto _300;
                case 0xD8: 
                case 0xD9: 
                case 0xDA: 
                case 0xDB: goto _293;
                case 0xDC: 
                case 0xDD: 
                case 0xDE: 
                case 0xDF: goto _300;

            }
        }
    } else {
        switch( input ) {
            case 0xE0: goto _297;
            case 0xE1: goto _295;
            case 0xE2: goto _299;
            case 0xE3: 
            case 0xE4: 
            case 0xE5: 
            case 0xE6: 
            case 0xE7: 
            case 0xE8: 
            case 0xE9: 
            case 0xEA: 
            case 0xEB: 
            case 0xEC: 
            case 0xED: 
            case 0xEE: 
            case 0xEF: goto _295;
            case 0xF0: goto _302;
            case 0xF1: goto _289;
            case 0xF2: 
            case 0xF3: goto _298;
            case 0xF4: goto _291;
            case 0xF5: 
            case 0xF6: 
            case 0xF7: goto _292;

        }
    }
    __quex_debug_drop_out(288);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_294: /* (294 from 323) (294 from 288) (294 from 300) (294 from 296) (294 from 309) (294 from 315) (294 from 312) */

    ++iterator;
    __quex_debug_state(294);
    __quex_debug_drop_out(294);
goto TERMINAL_19;

    __quex_assert_no_passage();
_300: /* (300 from 299) (300 from 288) (300 from 295) (300 from 297) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(300);
    if( input >= 0xC0 ) {

    } else if( input >= 0x80 ) {
        goto _294;
    } else {

    }
    __quex_debug_drop_out(300);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_309: /* (309 from 308) (309 from 322) (309 from 311) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(309);
    if( input >= 0xC0 ) {

    } else if( input >= 0x80 ) {
        goto _294;
    } else {

    }
    __quex_debug_drop_out(309);
goto TERMINAL_19;

    __quex_assert_no_passage();
_295: /* (295 from 288) (295 from 291) (295 from 292) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(295);
    if( input >= 0xC0 ) {

    } else if( input >= 0x80 ) {
        goto _300;
    } else {

    }
    __quex_debug_drop_out(295);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_303: /* (303 from 288) (303 from 312) (303 from 296) */

    ++iterator;
    __quex_debug_state(303);
    __quex_debug_drop_out(303);
goto TERMINAL_20;

    __quex_assert_no_passage();
_304: /* (304 from 289) (304 from 302) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(304);
    if( input >= 0xC0 ) {

    } else if( input >= 0x80 ) {
        goto _310;
    } else {

    }
    __quex_debug_drop_out(304);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_310: /* (310 from 320) (310 from 304) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(310);
    if( input >= 0xC0 ) {

    } else if( input >= 0x80 ) {
        goto _311;
    } else {

    }
    __quex_debug_drop_out(310);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_311: /* (311 from 321) (311 from 310) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(311);
    if( input >= 0xC0 ) {

    } else if( input >= 0x80 ) {
        goto _309;
    } else {

    }
    __quex_debug_drop_out(311);
goto TERMINAL_21;

    __quex_assert_no_passage();
_292: /* (292 from 288) (292 from 305) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(292);
    if( input >= 0xC0 ) {

    } else if( input >= 0x80 ) {
        goto _295;
    } else {

    }
    __quex_debug_drop_out(292);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_305: /* (305 from 302) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(305);
    if( input >= 0xC0 ) {

    } else if( input >= 0x80 ) {
        goto _292;
    } else {

    }
    __quex_debug_drop_out(305);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_306: /* (306 from 302) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(306);
    if( input >= 0xC0 ) {

    } else if( input >= 0x80 ) {
        goto _307;
    } else {

    }
    __quex_debug_drop_out(306);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_307: /* (307 from 306) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(307);
    if( input >= 0xC0 ) {

    } else if( input >= 0x80 ) {
        goto _308;
    } else {

    }
    __quex_debug_drop_out(307);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_308: /* (308 from 307) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(308);
    if( input >= 0xC0 ) {

    } else if( input >= 0x80 ) {
        goto _309;
    } else {

    }
    __quex_debug_drop_out(308);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_312: /* (312 from 299) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(312);
    switch( input ) {
        case 0x80: 
        case 0x81: 
        case 0x82: 
        case 0x83: 
        case 0x84: 
        case 0x85: 
        case 0x86: 
        case 0x87: 
        case 0x88: 
        case 0x89: 
        case 0x8A: 
        case 0x8B: 
        case 0x8C: 
        case 0x8D: 
        case 0x8E: 
        case 0x8F: 
        case 0x90: 
        case 0x91: 
        case 0x92: 
        case 0x93: 
        case 0x94: 
        case 0x95: 
        case 0x96: 
        case 0x97: 
        case 0x98: 
        case 0x99: 
        case 0x9A: 
        case 0x9B: 
        case 0x9C: 
        case 0x9D: 
        case 0x9E: 
        case 0x9F: 
        case 0xA0: 
        case 0xA1: 
        case 0xA2: 
        case 0xA3: 
        case 0xA4: 
        case 0xA5: 
        case 0xA6: 
        case 0xA7: goto _294;
        case 0xA8: 
        case 0xA9: goto _303;
        case 0xAA: 
        case 0xAB: 
        case 0xAC: 
        case 0xAD: 
        case 0xAE: 
        case 0xAF: 
        case 0xB0: 
        case 0xB1: 
        case 0xB2: 
        case 0xB3: 
        case 0xB4: 
        case 0xB5: 
        case 0xB6: 
        case 0xB7: 
        case 0xB8: 
        case 0xB9: 
        case 0xBA: 
        case 0xBB: 
        case 0xBC: 
        case 0xBD: 
        case 0xBE: 
        case 0xBF: goto _294;

    }
    __quex_debug_drop_out(312);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_313: /* (313 from 298) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(313);
    if( input >= 0xC0 ) {

    } else if( input >= 0x80 ) {
        goto _314;
    } else {

    }
    __quex_debug_drop_out(313);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_314: /* (314 from 313) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(314);
    if( input >= 0xC0 ) {

    } else if( input >= 0x80 ) {
        goto _315;
    } else {

    }
    __quex_debug_drop_out(314);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_315: /* (315 from 314) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(315);
    if( input >= 0xC0 ) {

    } else if( input >= 0x80 ) {
        goto _294;
    } else {

    }
    __quex_debug_drop_out(315);
goto TERMINAL_21;

    __quex_assert_no_passage();
_316: /* (316 from 293) */

    ++iterator;
    __quex_debug_state(316);
    __quex_debug_drop_out(316);
goto TERMINAL_18;

    __quex_assert_no_passage();
_317: /* (317 from 291) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(317);
    if( input >= 0xC0 ) {

    } else if( input >= 0x80 ) {
        goto _318;
    } else {

    }
    __quex_debug_drop_out(317);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_318: /* (318 from 317) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(318);
    if( input >= 0xC0 ) {

    } else if( input >= 0x80 ) {
        goto _319;
    } else {

    }
    __quex_debug_drop_out(318);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_319: /* (319 from 318) */

    ++iterator;
    __quex_debug_state(319);
    __quex_debug_drop_out(319);
goto TERMINAL_21;

    __quex_assert_no_passage();
_320: /* (320 from 289) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(320);
    switch( input ) {
        case 0x80: 
        case 0x81: 
        case 0x82: 
        case 0x83: 
        case 0x84: 
        case 0x85: 
        case 0x86: 
        case 0x87: 
        case 0x88: 
        case 0x89: 
        case 0x8A: 
        case 0x8B: 
        case 0x8C: 
        case 0x8D: 
        case 0x8E: 
        case 0x8F: 
        case 0x90: 
        case 0x91: 
        case 0x92: 
        case 0x93: 
        case 0x94: 
        case 0x95: 
        case 0x96: 
        case 0x97: 
        case 0x98: 
        case 0x99: 
        case 0x9A: 
        case 0x9B: 
        case 0x9C: 
        case 0x9D: 
        case 0x9E: 
        case 0x9F: 
        case 0xA0: 
        case 0xA1: 
        case 0xA2: 
        case 0xA3: 
        case 0xA4: 
        case 0xA5: 
        case 0xA6: 
        case 0xA7: 
        case 0xA8: 
        case 0xA9: 
        case 0xAA: 
        case 0xAB: 
        case 0xAC: 
        case 0xAD: 
        case 0xAE: 
        case 0xAF: 
        case 0xB0: 
        case 0xB1: 
        case 0xB2: 
        case 0xB3: 
        case 0xB4: 
        case 0xB5: 
        case 0xB6: 
        case 0xB7: 
        case 0xB8: 
        case 0xB9: 
        case 0xBA: 
        case 0xBB: 
        case 0xBC: 
        case 0xBD: 
        case 0xBE: goto _310;
        case 0xBF: goto _321;

    }
    __quex_debug_drop_out(320);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_321: /* (321 from 320) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(321);
    switch( input ) {
        case 0x80: 
        case 0x81: 
        case 0x82: 
        case 0x83: 
        case 0x84: 
        case 0x85: 
        case 0x86: 
        case 0x87: 
        case 0x88: 
        case 0x89: 
        case 0x8A: 
        case 0x8B: 
        case 0x8C: 
        case 0x8D: 
        case 0x8E: 
        case 0x8F: 
        case 0x90: 
        case 0x91: 
        case 0x92: 
        case 0x93: 
        case 0x94: 
        case 0x95: 
        case 0x96: 
        case 0x97: 
        case 0x98: 
        case 0x99: 
        case 0x9A: 
        case 0x9B: 
        case 0x9C: 
        case 0x9D: 
        case 0x9E: 
        case 0x9F: 
        case 0xA0: 
        case 0xA1: 
        case 0xA2: 
        case 0xA3: 
        case 0xA4: 
        case 0xA5: 
        case 0xA6: 
        case 0xA7: 
        case 0xA8: 
        case 0xA9: 
        case 0xAA: 
        case 0xAB: 
        case 0xAC: 
        case 0xAD: 
        case 0xAE: 
        case 0xAF: 
        case 0xB0: 
        case 0xB1: 
        case 0xB2: 
        case 0xB3: 
        case 0xB4: 
        case 0xB5: 
        case 0xB6: 
        case 0xB7: 
        case 0xB8: 
        case 0xB9: 
        case 0xBA: 
        case 0xBB: 
        case 0xBC: 
        case 0xBD: 
        case 0xBE: goto _311;
        case 0xBF: goto _322;

    }
    __quex_debug_drop_out(321);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_322: /* (322 from 321) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(322);
    switch( input ) {
        case 0x80: 
        case 0x81: 
        case 0x82: 
        case 0x83: 
        case 0x84: 
        case 0x85: 
        case 0x86: 
        case 0x87: 
        case 0x88: 
        case 0x89: 
        case 0x8A: 
        case 0x8B: 
        case 0x8C: 
        case 0x8D: 
        case 0x8E: 
        case 0x8F: 
        case 0x90: 
        case 0x91: 
        case 0x92: 
        case 0x93: 
        case 0x94: 
        case 0x95: 
        case 0x96: 
        case 0x97: 
        case 0x98: 
        case 0x99: 
        case 0x9A: 
        case 0x9B: 
        case 0x9C: 
        case 0x9D: 
        case 0x9E: 
        case 0x9F: 
        case 0xA0: 
        case 0xA1: 
        case 0xA2: 
        case 0xA3: 
        case 0xA4: 
        case 0xA5: 
        case 0xA6: 
        case 0xA7: 
        case 0xA8: 
        case 0xA9: 
        case 0xAA: 
        case 0xAB: 
        case 0xAC: 
        case 0xAD: 
        case 0xAE: 
        case 0xAF: 
        case 0xB0: 
        case 0xB1: 
        case 0xB2: 
        case 0xB3: 
        case 0xB4: 
        case 0xB5: 
        case 0xB6: 
        case 0xB7: 
        case 0xB8: 
        case 0xB9: 
        case 0xBA: 
        case 0xBB: 
        case 0xBC: 
        case 0xBD: 
        case 0xBE: goto _309;
        case 0xBF: goto _323;

    }
    __quex_debug_drop_out(322);
goto TERMINAL_21;

    __quex_assert_no_passage();
_323: /* (323 from 322) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(323);
    if( input >= 0xBF ) {

    } else if( input >= 0x80 ) {
        goto _294;
    } else {

    }
    __quex_debug_drop_out(323);
goto TERMINAL_19;

    __quex_assert_no_passage();
_289: /* (289 from 288) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(289);
    switch( input ) {
        case 0x80: 
        case 0x81: 
        case 0x82: 
        case 0x83: 
        case 0x84: 
        case 0x85: 
        case 0x86: 
        case 0x87: 
        case 0x88: 
        case 0x89: 
        case 0x8A: 
        case 0x8B: 
        case 0x8C: 
        case 0x8D: 
        case 0x8E: 
        case 0x8F: 
        case 0x90: 
        case 0x91: 
        case 0x92: 
        case 0x93: 
        case 0x94: 
        case 0x95: 
        case 0x96: 
        case 0x97: 
        case 0x98: 
        case 0x99: 
        case 0x9A: 
        case 0x9B: 
        case 0x9C: 
        case 0x9D: 
        case 0x9E: 
        case 0x9F: 
        case 0xA0: 
        case 0xA1: 
        case 0xA2: 
        case 0xA3: 
        case 0xA4: 
        case 0xA5: 
        case 0xA6: 
        case 0xA7: 
        case 0xA8: 
        case 0xA9: 
        case 0xAA: 
        case 0xAB: 
        case 0xAC: 
        case 0xAD: 
        case 0xAE: 
        case 0xAF: 
        case 0xB0: 
        case 0xB1: 
        case 0xB2: 
        case 0xB3: 
        case 0xB4: 
        case 0xB5: 
        case 0xB6: 
        case 0xB7: 
        case 0xB8: 
        case 0xB9: 
        case 0xBA: 
        case 0xBB: 
        case 0xBC: 
        case 0xBD: 
        case 0xBE: goto _304;
        case 0xBF: goto _320;

    }
    __quex_debug_drop_out(289);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_290: /* (290 from 288) */

    ++iterator;
    __quex_debug_state(290);
    __quex_debug_drop_out(290);
goto TERMINAL_17;

    __quex_assert_no_passage();
_291: /* (291 from 288) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(291);
    switch( input ) {
        case 0x80: 
        case 0x81: 
        case 0x82: 
        case 0x83: 
        case 0x84: 
        case 0x85: 
        case 0x86: 
        case 0x87: 
        case 0x88: 
        case 0x89: 
        case 0x8A: 
        case 0x8B: 
        case 0x8C: 
        case 0x8D: 
        case 0x8E: 
        case 0x8F: goto _317;
        case 0x90: 
        case 0x91: 
        case 0x92: 
        case 0x93: 
        case 0x94: 
        case 0x95: 
        case 0x96: 
        case 0x97: 
        case 0x98: 
        case 0x99: 
        case 0x9A: 
        case 0x9B: 
        case 0x9C: 
        case 0x9D: 
        case 0x9E: 
        case 0x9F: 
        case 0xA0: 
        case 0xA1: 
        case 0xA2: 
        case 0xA3: 
        case 0xA4: 
        case 0xA5: 
        case 0xA6: 
        case 0xA7: 
        case 0xA8: 
        case 0xA9: 
        case 0xAA: 
        case 0xAB: 
        case 0xAC: 
        case 0xAD: 
        case 0xAE: 
        case 0xAF: 
        case 0xB0: 
        case 0xB1: 
        case 0xB2: 
        case 0xB3: 
        case 0xB4: 
        case 0xB5: 
        case 0xB6: 
        case 0xB7: 
        case 0xB8: 
        case 0xB9: 
        case 0xBA: 
        case 0xBB: 
        case 0xBC: 
        case 0xBD: 
        case 0xBE: 
        case 0xBF: goto _295;

    }
    __quex_debug_drop_out(291);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_293: /* (293 from 288) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(293);
    if( input >= 0xC0 ) {

    } else if( input >= 0x80 ) {
        goto _316;
    } else {

    }
    __quex_debug_drop_out(293);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_296: /* (296 from 288) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(296);
    switch( input ) {
        case 0x80: 
        case 0x81: 
        case 0x82: 
        case 0x83: 
        case 0x84: goto _294;
        case 0x85: goto _303;
        case 0x86: 
        case 0x87: 
        case 0x88: 
        case 0x89: 
        case 0x8A: 
        case 0x8B: 
        case 0x8C: 
        case 0x8D: 
        case 0x8E: 
        case 0x8F: 
        case 0x90: 
        case 0x91: 
        case 0x92: 
        case 0x93: 
        case 0x94: 
        case 0x95: 
        case 0x96: 
        case 0x97: 
        case 0x98: 
        case 0x99: 
        case 0x9A: 
        case 0x9B: 
        case 0x9C: 
        case 0x9D: 
        case 0x9E: 
        case 0x9F: 
        case 0xA0: 
        case 0xA1: 
        case 0xA2: 
        case 0xA3: 
        case 0xA4: 
        case 0xA5: 
        case 0xA6: 
        case 0xA7: 
        case 0xA8: 
        case 0xA9: 
        case 0xAA: 
        case 0xAB: 
        case 0xAC: 
        case 0xAD: 
        case 0xAE: 
        case 0xAF: 
        case 0xB0: 
        case 0xB1: 
        case 0xB2: 
        case 0xB3: 
        case 0xB4: 
        case 0xB5: 
        case 0xB6: 
        case 0xB7: 
        case 0xB8: 
        case 0xB9: 
        case 0xBA: 
        case 0xBB: 
        case 0xBC: 
        case 0xBD: 
        case 0xBE: 
        case 0xBF: goto _294;

    }
    __quex_debug_drop_out(296);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_297: /* (297 from 288) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(297);
    switch( input ) {
        case 0xA0: 
        case 0xA1: 
        case 0xA2: 
        case 0xA3: 
        case 0xA4: 
        case 0xA5: 
        case 0xA6: 
        case 0xA7: 
        case 0xA8: 
        case 0xA9: 
        case 0xAA: 
        case 0xAB: 
        case 0xAC: 
        case 0xAD: 
        case 0xAE: 
        case 0xAF: 
        case 0xB0: 
        case 0xB1: 
        case 0xB2: 
        case 0xB3: 
        case 0xB4: 
        case 0xB5: 
        case 0xB6: 
        case 0xB7: 
        case 0xB8: 
        case 0xB9: 
        case 0xBA: 
        case 0xBB: 
        case 0xBC: 
        case 0xBD: 
        case 0xBE: 
        case 0xBF: goto _300;

    }
    __quex_debug_drop_out(297);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_298: /* (298 from 288) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(298);
    if( input >= 0xC0 ) {

    } else if( input >= 0x80 ) {
        goto _313;
    } else {

    }
    __quex_debug_drop_out(298);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_299: /* (299 from 288) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(299);
    switch( input ) {
        case 0x80: goto _312;
        case 0x81: 
        case 0x82: 
        case 0x83: 
        case 0x84: 
        case 0x85: 
        case 0x86: 
        case 0x87: 
        case 0x88: 
        case 0x89: 
        case 0x8A: 
        case 0x8B: 
        case 0x8C: 
        case 0x8D: 
        case 0x8E: 
        case 0x8F: 
        case 0x90: 
        case 0x91: 
        case 0x92: 
        case 0x93: 
        case 0x94: 
        case 0x95: 
        case 0x96: 
        case 0x97: 
        case 0x98: 
        case 0x99: 
        case 0x9A: 
        case 0x9B: 
        case 0x9C: 
        case 0x9D: 
        case 0x9E: 
        case 0x9F: 
        case 0xA0: 
        case 0xA1: 
        case 0xA2: 
        case 0xA3: 
        case 0xA4: 
        case 0xA5: 
        case 0xA6: 
        case 0xA7: 
        case 0xA8: 
        case 0xA9: 
        case 0xAA: 
        case 0xAB: 
        case 0xAC: 
        case 0xAD: 
        case 0xAE: 
        case 0xAF: 
        case 0xB0: 
        case 0xB1: 
        case 0xB2: 
        case 0xB3: 
        case 0xB4: 
        case 0xB5: 
        case 0xB6: 
        case 0xB7: 
        case 0xB8: 
        case 0xB9: 
        case 0xBA: 
        case 0xBB: 
        case 0xBC: 
        case 0xBD: 
        case 0xBE: 
        case 0xBF: goto _300;

    }
    __quex_debug_drop_out(299);

goto _325; /* TERMINAL_FAILURE */

    __quex_assert_no_passage();
_301: /* (301 from 288) */

    ++iterator;
    __quex_debug_state(301);
    __quex_debug_drop_out(301);
goto TERMINAL_16;

    __quex_assert_no_passage();
_302: /* (302 from 288) */

    ++iterator;
    input = *iterator;
    __quex_debug_state(302);
    switch( input ) {
        case 0x84: 
        case 0x85: 
        case 0x86: 
        case 0x87: goto _305;
        case 0x88: 
        case 0x89: 
        case 0x8A: 
        case 0x8B: 
        case 0x8C: 
        case 0x8D: 
        case 0x8E: 
        case 0x8F: goto _306;
        case 0x90: 
        case 0x91: 
        case 0x92: 
        case 0x93: 
        case 0x94: 
        case 0x95: 
        case 0x96: 
        case 0x97: 
        case 0x98: 
        case 0x99: 
        case 0x9A: 
        case 0x9B: 
        case 0x9C: 
        case 0x9D: 
        case 0x9E: 
        case 0x9F: 
        case 0xA0: 
        case 0xA1: 
        case 0xA2: 
        case 0xA3: 
        case 0xA4: 
        case 0xA5: 
        case 0xA6: 
        case 0xA7: 
        case 0xA8: 
        case 0xA9: 
        case 0xAA: 
        case 0xAB: 
        case 0xAC: 
        case 0xAD: 
        case 0xAE: 
        case 0xAF: 
        case 0xB0: 
        case 0xB1: 
        case 0xB2: 
        case 0xB3: 
        case 0xB4: 
        case 0xB5: 
        case 0xB6: 
        case 0xB7: 
        case 0xB8: 
        case 0xB9: 
        case 0xBA: 
        case 0xBB: 
        case 0xBC: 
        case 0xBD: 
        case 0xBE: 
        case 0xBF: goto _304;

    }
    __quex_debug_drop_out(302);

goto _325; /* TERMINAL_FAILURE */
TERMINAL_16:
        __quex_debug("* terminal 16:   \n");
        __QUEX_IF_COUNT_COLUMNS_SET((size_t)1);

TERMINAL_17:
        __quex_debug("* terminal 17:   \n");
                __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end &= ~ ((size_t)0x3));
        __QUEX_IF_COUNT_COLUMNS(self.counter._column_number_at_end += 4);

TERMINAL_18:
        __quex_debug("* terminal 18:   \n");
        __QUEX_IF_COUNT_COLUMNS_ADD((size_t)3);

TERMINAL_19:
        __quex_debug("* terminal 19:   \n");
        __QUEX_IF_COUNT_COLUMNS_ADD((size_t)1);

TERMINAL_20:
        __quex_debug("* terminal 20:   \n");
        __QUEX_IF_COUNT_LINES_ADD((size_t)1);
        __QUEX_IF_COUNT_COLUMNS_SET((size_t)1);

TERMINAL_21:
        __quex_debug("* terminal 21:   \n");
        __QUEX_IF_COUNT_COLUMNS_ADD((size_t)2);


_325: /* TERMINAL: FAILURE */
    
        QUEX_ERROR_EXIT("State machine failed.");

    }
    __quex_assert(iterator == LexemeEnd); /* Otherwise, lexeme violates codec character boundaries. */
#   undef self
}
#endif /* __QUEX_OPTION_COUNTER */