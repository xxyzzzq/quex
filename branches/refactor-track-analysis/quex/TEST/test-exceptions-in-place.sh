#! /usr/bin/env bash
if [[ $1 == "--hwut-info" ]]; then
    echo "Double Check that Exception Handlers are in place;"
    exit
fi
echo "(*) Exceptions during 'import'"

for x in AssertionError KeyboardInterrupt Exception; do
    echo "  -- $x:"
    quex '<<TEST:Exceptions/on-import>>' $x
    echo
done

echo "(*) Exceptions during 'function'"

for x in AssertionError KeyboardInterrupt Exception; do
    echo "  -- $x:"
    quex '<<TEST:Exceptions/function>>' $x
    echo
done
