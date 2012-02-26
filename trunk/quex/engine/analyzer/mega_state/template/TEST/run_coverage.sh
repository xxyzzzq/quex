SOURCE="--source quex.engine.analyzer.template "
for arg in 1 2 2b 3 4 recursive recursive-b; do
    coverage run -a $SOURCE combine-maps.py $arg 
done

for arg in 1 2 recursive recursive-2 recursive-2b recursive-3 recursive-b recursive-3b; do
    coverage run -a $SOURCE combine-maps-2.py $arg 
done

for arg in 0 1 2 3; do
    coverage run -a $SOURCE ./best_matching_pair.py $arg 
done

for arg in 1 2 2b 3 4 recursive; do
    coverage run -a $SOURCE metric.py $arg 
done
