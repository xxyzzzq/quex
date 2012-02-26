SOURCE="--source quex.engine.analyzer.path "
for arg in 0 1 2 3 4 5a 5b 6; do
    coverage run -a $SOURCE filter_redundant_paths.py $arg 
done

for arg in `seq 1 6`; do
    coverage run -a $SOURCE find.py $arg 
done

for arg in `seq 1 3`; do
    coverage run -a $SOURCE find-2.py $arg 
done

for arg in 1_interval 2_interval; do
    coverage run -a $SOURCE can_plug_to_equal.py $arg 
done

for arg in `seq 0 5`; do
    echo $arg
    coverage run -a $SOURCE select_longest_paths.py $arg 
done
