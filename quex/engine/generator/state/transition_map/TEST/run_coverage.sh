SOURCE="--source quex.engine.generator.state.transition_map "

coverage run -a $SOURCE test-bisection.py 
for choice in C-2 C-3 C-4 C-5; do
    coverage run -a $SOURCE test-branch_table.py $choice
done
for choice in C-7 C-8 C-9 C-15 C-16 C-17 C-31 C-32 C-33; do
    coverage run -a $SOURCE test-branch_table-2.py $choice
done
for choice in C-2-fw C-2-fw C-3-fw C-3-bw C-4-fw C-4-bw C-5-fw C-5-bw; do
    coverage run -a $SOURCE test-comparison_sequence.py $choice
done
