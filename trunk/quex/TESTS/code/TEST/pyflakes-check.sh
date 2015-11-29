
case $1 in
    --hwut-info)
        echo "Code Check with pyflakes"
        ;;
    *)
        echo "No output is good output"
        for file in `find $QUEX_PATH/quex -path "*TEST*" -prune -or -name "*.py" -print`; do
            echo "## FILE: $file"
            pyflakes $file
        done
esac
