#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.regular_expression.engine      as regex
import quex.core_engine.state_machine.identity_checker as identity_checker

if "--hwut-info" in sys.argv:
    print "Pattern Identity Determination"
    print "CHOICES: True, False, Pre-Post-Contexts-True, Pre-Post-Contexts-False;"
    sys.exit(0)
    
def test(A, B):
    def __core(Pattern0, Pattern1):
        print ("Pattern0 = " + Pattern0).replace("\n", "\\n").replace("\t", "\\t")
        print ("Pattern1 = " + Pattern1).replace("\n", "\\n").replace("\t", "\\t")
        sm0 = regex.do(Pattern0, {})
        sm1 = regex.do(Pattern1, {})
        print "claim = ", identity_checker.do(sm0, sm1)
    print "---------------------------"
    __core(A, B)
    print
    __core(B, A)

if "True" in sys.argv:
    test('[A-MO-RT-Z][a-z]*',  '[A-MO-RT-Z][a-z]*')
    test('[abd-fh-z][a-z]*',   '[abd-fh-z][a-z]*')
    test('12(A(B?)C|DE(F?))+', '12(DE(F?)|A(B?)C)+')
    test('12((B?)|(F?))34',    '12[BF]?34')
    test('[a-cx-z]*((B?)|(F?))34', '(a?|b?|c?|x?|y?|z?)+[BF]?34')
    test('[a-c]?A', '(a?|b|c)A')
    print "NOTE: The '?' creates a 'free path' so that 'a?|b' is equivalent to 'a?|b?' and '[ab]?'"
    test('12((A?|D)(A?|E))*34',                  '12((A?|E)(A?|D))+34')
    test('12(("Alf"?|"Didi")("Alf"?|"Elf"))*34', '12(("Alf"?|"Elf")("Alf"?|"Didi"))+34')
    test('12((A?|D|E))*34',                      '12((A?|E)(A?|D))+34')

elif "False" in sys.argv:
    test('[A-MP-RT-Z][a-z]*',  '[A-MO-RT-Z][a-z]*')
    test('[abd-fh-z][a-y]*',   '[abd-fh-z][a-z]*')
    test('12(A(B?)C|DEF)+',    '12(DE(F?)|A(B?)C)+')
    test('"123"+',  '"123"')
    test('"123"*X', '"123"X')
    test('12((A?|D|E))+34',    '12((A?|E)(A|D))+34')

elif "Pre-Post-Contexts-False" in sys.argv:
    # with pre and post-conditions
    test('A/B',      'AB')
    test('A/B/',     'B')
    test('A/B(C?)/', 'A/B/')
    test('A/B(C?)/', 'A+/B/')
    test('B$',  'B')
    test('^B',  'B')

elif "Pre-Post-Contexts-True" in sys.argv:
    # with pre and post-conditions
    test('A/B',      'A/B')
    test('A/B/',     'A/B/')
    test('A/B/C',    'A/B/C')
    test('B$',  'B$')
    test('^B',  '^B')
