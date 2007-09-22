import re
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.frs_py.file_in         import *
from quex.frs_py.string_handling import *

from quex.core_engine.interval_handling import Interval


comment_deleter_re = re.compile("#[^\n]*")

def get_table(Filename):
    fh = open(Filename)
    if fh == 0:
        raise BaseException("Trying to read unicode database file '%s' but file could not be opened." %\
                             Filename)

    record_set = []
    for line in fh.readlines():
        line = trim(line)
        line = comment_deleter_re.sub("", line)
        if line.isspace() or line == "": continue
        # append content to record set
        record_set.append(map(trim, line.split(";")))

    return record_set

def __convert_column_to_interval(table, ColumnN):

    for row in table:
        cell = row[ColumnN]
        fields = cell.split("..")
        assert len(fields) in [1, 2]

        if len(fields) == 2: 
           begin = int("0x" + fields[0], 16)
           end   = int("0x" + fields[1], 16) + 1
        else:
           begin = int("0x" + fields[0], 16)
           end   = int("0x" + fields[0], 16) + 1

        row[ColumnN] = Interval(begin, end)

blocks_db = None

def __init_block_db():
    global blocks_db
    table = get_table("Blocks.txt")

    # the first elements of the table are ranges, so make them intervals
    __convert_column_to_interval(table, 0)
    blocks_db = table

def get_block(Blockname):
    if block_db == None: __init_block_db()
        
    
__init_block_db() 
print blocks_db
