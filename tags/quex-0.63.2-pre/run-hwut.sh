# touch A.tmp; hwut TEST/ >& A.log; rm A.tmp &
# B { hwut demo/Cpp/TEST/ >& B.log; }
# C { hwut demo/C/TEST/   >& C.log; }
# D { hwut quex/          >& D.log; }

function run_this {
    pwd
    touch $1.tmp
    echo "start $2"
    hwut  $2 >& /dev/null
    # sleep 10
    echo "end $2"
    rm    $1.tmp
}

echo
run_this A TEST/          &
run_this B demo/Cpp/TEST/ &
run_this C demo/C/TEST/   &
run_this D quex/          &

while [ ! -e A.tmp -o ! -e B.tmp -o ! -e C.tmp -o ! -e D.tmp ]; do 
    echo "Wait to begin"
    sleep 1
done

ls *.tmp

# Wait until all are finished
while [ -e A.tmp -o -e B.tmp -o -e C.tmp -o -e D.tmp ]; do 
    echo "Wait to terminate"
    sleep 1
done
