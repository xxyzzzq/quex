#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.misc.interval_handling                   import Interval
from   quex.engine.state_machine.transformation.TEST.helper import test_plug_sequence as test

from   quex.blackboard import setup as Setup

Setup.bad_lexatom_detection_f = True

if "--hwut-info" in sys.argv:
    print "State Split: Plug Interval Sequence - With BL Detection;"
    print "CHOICES: 1.1, 1.2, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4;"
    sys.exit(0)

# 0x00000000 - 0x0000007F: 1 byte  - 0xxxxxxx
# 0x00000080 - 0x000007FF: 2 bytes - 110xxxxx 10xxxxxx
# 0x00000800 - 0x0000FFFF: 3 bytes - 1110xxxx 10xxxxxx 10xxxxxx
# 0x00010000 - 0x001FFFFF: 4 bytes - 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
# 0x00200000 - 0x03FFFFFF: 5 bytes ... 
# 0x04000000 - 0x7FFFFFFF: 
if "4.1" in sys.argv:
    test([[Interval(0xF1), Interval(0x82), Interval(0x82), Interval(0xAE, 0xC0)],
          [Interval(0xF1), Interval(0x82), Interval(0x83), Interval(0x80, 0xC0)],
          [Interval(0xF1), Interval(0x82), Interval(0x84), Interval(0x80, 0xA1)]])

elif "4.2" in sys.argv:
    test([[Interval(0xF1), Interval(0x80), Interval(0x80),       Interval(0x80, 0xC0)],
          [Interval(0xF1), Interval(0x81), Interval(0x81, 0xC0), Interval(0x80, 0xC0)],
          [Interval(0xF1), Interval(0x82), Interval(0x80, 0x84), Interval(0x80, 0xC0)]])

elif "4.3" in sys.argv:
    test([[Interval(0xF0), Interval(0x80, 0xC0), Interval(0x80, 0xC0), Interval(0x80, 0xC0)],
          [Interval(0xF1), Interval(0x80, 0xC0), Interval(0x80, 0xC0), Interval(0x80, 0xC0)],
          [Interval(0xF2), Interval(0x82),       Interval(0x80, 0xBF), Interval(0x80, 0xC0)]])

elif "4.4" in sys.argv:
    test([[Interval(0xF0), Interval(0x81),  Interval(0x80),       Interval(0x83, 0xC0)],
          [Interval(0xF0), Interval(0x81),  Interval(0x81, 0xC0), Interval(0x80, 0xC0)],
          [Interval(0xF2), Interval(0x82),  Interval(0x80, 0xC0), Interval(0x80, 0xC0)],
          [Interval(0xF2), Interval(0x83),  Interval(0x80, 0xC0), Interval(0x80, 0x81)]])

elif "1.1" in sys.argv:
    test([[Interval(0xF0), ],
          [Interval(0xF1), ],
          [Interval(0xF2), ]])

elif "1.2" in sys.argv:
    test([[Interval(0x00, 0x80)]])

elif "2.1" in sys.argv:
    test([[Interval(0x00, 0x80), Interval(0x80, 0xC0)]])

elif "2.2" in sys.argv:
    test([[Interval(0x00, 0x70), Interval(0x80, 0xC0)],
          [Interval(0x71),       Interval(0x80, 0xC0)],
          ])

elif "2.3" in sys.argv:
    test([[Interval(0x00, 0x71), Interval(0x81, 0xC0)],
          [Interval(0x71),       Interval(0x80, 0xC0)],
          ])
# 3 Intervals
elif "3.1" in sys.argv:
    test([[Interval(0x00, 0x80), Interval(0x80, 0xC0), Interval(0x80, 0xC0)]])

elif "3.2" in sys.argv:
    test([[Interval(0x00, 0x70), Interval(0x80, 0xC0), Interval(0x80, 0xC0)],
          [Interval(0x71),       Interval(0x80, 0xC0), Interval(0x80, 0xC0)],
          ])

elif "3.3" in sys.argv:
    test([[Interval(0x00, 0x70), Interval(0x80, 0xC0), Interval(0x80, 0xC0)],
          [Interval(0x71),       Interval(0x80, 0xC0), Interval(0x80, 0xC0)],
          [Interval(0x72),       Interval(0x80, 0x81), Interval(0x80, 0xBF)],
          ])
