if [[ "$1" = "--hwut-info" ]]; then
    echo "With Errors;"
    exit
fi


function test {
    echo "    File: 'good-$1.qx': {"
    rm -f TmpLex*
    quex -i bad-$1.qx -o TmpLex |& awk '{ print "        " $0; }'
    if [ -e TmpLex ]; then echo Files generated with incorrect configuration; exit; fi
    echo "    }"
    echo 
}

echo "(1) A <-> B"
echo "    not all implicit transitions allowed explicitly"
test 1

echo "(2) A <-> B"
echo "    not all explicit transitions allowed explicitly"
test 2

echo "(3) A1 derived from A;" 
echo "    A1 -> Z; A -> Z;" 
echo "    Z -> A;" 
echo "    Entry A -> Z disallowed; Entry A1 -> Z allowed"
test 3

echo "(4) A1 derived from A;" 
echo "    A1 -> Z;" 
echo "    Z -> A1;"
echo "    A inheritable only; Z disallows entry from A1"
test 4

echo "(5) Derived mode inherits entry permissions from base"
test 5

echo "(6) Inclusive aggregation of exit permissions"
test 6

echo "(7) Exclusive aggregation of entry permissions"
test 7

echo "(8) Exit mode does not exist"
test 8

echo "(9) Entry mode does not exist"
test 9



echo "<terminated>"
