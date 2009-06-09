import os
import sys
sys.path.append(os.environ["QUEX_PATH"])

import quex.input.codec_db as codec_db

def do(sm, CodecName, FH=-1, LineN=None):
    """Arguments FH and LineN are according to error_msg(..)"""
    trafo_info = codec_db.get_codec_transformation_info(CodecName)
    
    sm.transform(trafo_info)



