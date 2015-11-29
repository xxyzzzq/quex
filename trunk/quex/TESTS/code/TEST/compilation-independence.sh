#! /usr/bin/bash 

if [[ $1 == "--hwut-info" ]]; then
    echo "Do code base file compile independently?"
    exit
fi

here=`pwd`

cd $QUEX_PATH/quex/code_base

for file in `find -path "*.svn*" -or -path "*TEST*" -or -name tags -or -name "TXT*" -or -name "*.txt" -or -name "*.sw?" -or -path "*DESIGN*" -or -name "*.7z" -or -name "*.qx" -or -name "*ignore" -or -name "*DELETED*" -or -name . -or -name "*_body" -or -name "*.g*" -or -name "[1-9]" -or -name "°" -or -name "*.o" -or -name "*.exe" -prune -or -type f -print | sort`; do

    case $file in

        *.i)
        ;;

        *)
            echo "COMPILE: $file ____________________________________________"
            cat  $QUEX_PATH/quex/code_base/test_environment/TestAnalyzer-configuration > $here/tmp.cpp
            cat  $file >> $here/tmp.cpp
            g++  $here/tmp.cpp -I$QUEX_PATH -c 
        ;;

    esac

    if [[ $file == "X./analyzer/Accumulator.i" ]]; then
        break
    fi
done

cd $here
