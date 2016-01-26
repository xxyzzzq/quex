if [[ "$1" = "--hwut-info" ]]; then
    echo "Without Errors;"
    exit
fi


function test {
    echo "    File: 'good-$1.qx': {"
    echo "        (No Output is Good Output)"
    quex -i good-$1.qx -o TmpLex
    if [ ! -e TmpLex ]; then echo No files generated; exit; fi
    rm -f TmpLex*
    echo "    }"
    echo 
}

echo "(1) A <-> B"
echo "    all transitions allowed explicitly"
test 1

echo "(2) A <-> B"
echo "    only required transitions allowed explicitly"
test 2

echo "(3) A1 derived from A;" 
echo "    A1 -> Z; A -> Z;" 
echo "    Z -> A;" 
echo "    explicit permissions"
test 3

echo "(4) A1 derived from A;" 
echo "    A1 -> Z;" 
echo "    Z -> A1;"
echo "    A inheritable only; explicit permissions"
test 4

echo "(5) Derived mode inherits entry permissions from base"
test 5

echo "(6) Derived mode inherits exit permissions from base"
test 6

echo "(7) Exclusive aggregation of entry permissions"
test 7

echo "(8) Inclusive aggregation of exit permissions"
test 8



echo "<terminated>"
