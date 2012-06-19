SOURCE="--source quex.engine.analyzer.mega_state.path_walker "

for arg in `seq 1 6`; do
    coverage run -a $SOURCE find.py $arg 
done

for arg in `seq 1 3`; do
    coverage run -a $SOURCE find-2.py $arg 
done

for arg in 1_interval 2_interval; do
    coverage run -a $SOURCE can_plug_to_equal.py $arg 
done

for arg in `seq 0 10` 11a 11b 12; do
    echo $arg
    coverage run -a $SOURCE select_longest_paths.py $arg 
done
