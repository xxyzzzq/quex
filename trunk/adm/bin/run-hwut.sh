# touch A.tmp; hwut TEST/ >& A.log; rm A.tmp &
# B { hwut demo/Cpp/TEST/ >& B.log; }
# C { hwut demo/C/TEST/   >& C.log; }
# D { hwut quex/          >& D.log; }

function run_this {
    pwd
    echo "start $2"
    hwut  $2 >& $1
    echo "end $2"
}

echo
rm -f A.tmp B.tmp. C.tmp D.tmp

dir_list="TEST/ demo/Cpp/TEST demo/C/TEST quex/"

echo "Collecting Info"
index=0
for directory in $dir_list; do
    index=$(($index + 1))
    hwut i $directory > hwut_$index.previous
done

echo "Start Test Processes"
index=0
for directory in $dir_list; do
    index=$(($index + 1))
    run_this hwut_$index.result $directory &
done

echo "Wait to begin"
while [ ! -e hwut_1.result ! -o -e hwut_2.result -o ! -e hwut_3.result -o ! -e hwut_4.result ]; do 
    sleep 1
done

echo "All Started"
# Wait until all are finished
while [ -e hwut_1.result -o -e hwut_2.result -o -e hwut_3.result -o -e hwut_4.result ]; do 
    sleep 1
    index=0
    for directory in $dir_list; do
        index=$(($index + 1))
        size0=$(stat -c%s "hwut_$index.previous")
        size1=$(stat -c%s "hwut_$index.result")
        percent[$index]=$(( ($size1 * 100) / ($size0 * 100) ))
    done
    echo "${percent[1]} ${percent[2]} ${percent[3]} ${percent[4]}"
done

index=0
for directory in $dir_list; do
    index=$(($index + 1))
    rm -f hwut_$index.previous
    rm -f hwut_$index.result
done
