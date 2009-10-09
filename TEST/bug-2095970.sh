#! /usr/bin/env bash
#
bug=2095970
if [[ $1 == "--hwut-info" ]]; then
    echo "sphericalcow: $bug 0.31.3 Mode change without immediate return"
    echo "CHOICES: Normal, NormalNoAsserts, NoModeDetection, NoModeDetectionNoAsserts, NoModeDetection_ErrorCase;"
    exit
fi

tmp=`pwd`
cd $bug/ 
make clean >& /dev/null


if [[ $1 == "Normal" ]]; then
    make EXT_MODE_FILE=with-mode-change-detection.qx 
fi
if [[ $1 == "NormalNoAsserts" ]]; then
    make EXT_MODE_FILE=with-mode-change-detection.qx \
         EXT_CFLAGS=-DQUEX_OPTION_ASSERTS_DISABLED     
fi
if [[ $1 == "NoModeDetection" ]]; then
    make EXT_MODE_FILE=without-mode-change-detection.qx \
         EXT_CFLAGS=-DQUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE_DISABLED
fi
if [[ $1 == "NoModeDetectionNoAsserts" ]]; then
    make EXT_MODE_FILE=without-mode-change-detection.qx \
         EXT_CFLAGS='-DQUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE_DISABLED -DQUEX_OPTION_ASSERTS_DISABLED'
fi
if [[ $1 == "NoModeDetection_ErrorCase" ]]; then
    make EXT_MODE_FILE=with-mode-change-detection.qx \
         EXT_CFLAGS='-DQUEX_OPTION_AUTOMATIC_ANALYSIS_CONTINUATION_ON_MODE_CHANGE_DISABLED'
fi

./lexer >& tmp.txt
cat tmp.txt
rm tmp.txt
# cleansening
make clean
cd $tmp
