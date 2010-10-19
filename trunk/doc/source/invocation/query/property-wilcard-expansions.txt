Property Wildcard Expressions
=============================

Property value settings can be specified using wildcards as 
explained in <<sec-formal/patterns/character-set>>. Using
the command line option ``--property-match`` allows the user to see
to which values these wildcard expressions actually expand.
For example, the call

.. code-block:: bash

   > quex --property-match Name=MATH*FIVE*

delivers:

.. code-block:: bash

    MATHEMATICAL_BOLD_DIGIT_FIVE
    MATHEMATICAL_DOUBLE-STRUCK_DIGIT_FIVE
    MATHEMATICAL_MONOSPACE_DIGIT_FIVE
    MATHEMATICAL_SANS-SERIF_BOLD_DIGIT_FIVE
    MATHEMATICAL_SANS-SERIF_DIGIT_FIVE

Note, that the final character sets spanned by these settings can be viewed
using ``--set-by-property Name=MATH*FIVE*`` and ``--set-by-expression \N{MATH*FIVE*}``
in the manner previously explained. For example, 


.. code-block:: bash

   > quex --set-by-property 'Name=MATH*FIVE*'

delivers:

.. code-block:: bash

    1D7D0:             1D7D3 
    1D7D8:                         1D7DD 
    1D7E0:                                     1D7E7 
    ...
    1D7F0: 1D7F1 
    1D7F8:             1D7FB



