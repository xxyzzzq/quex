cp example.txt example-1kB.txt
# from 1 to 64KB create files for each KB
j=1; for i in `seq 2 64`; do cat example.txt example-${j}kB.txt > example-${i}kB.txt; j=$i; done

# from 64KB to 1MB create files of 64KB increment
mv example-64kB.txt example-1x64kB.txt
j=1; for i in `seq 2 16`; do cat example-1x64kB.txt example-${j}x64kB.txt > example-${i}x64kB.txt; j=$i; done

# from 1MB to 32MB create files of 1MB increment
mv example-16x64kB.txt example-1MB.txt
j=1; for i in `seq 2 32`; do cat example-1MB.txt example-${j}MB.txt > example-${i}MB.txt; j=$i; done

touch EXAMPLE-DB-CREATED
