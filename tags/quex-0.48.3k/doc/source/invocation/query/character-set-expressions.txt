Character Set Expressions
=========================

The specification of character sets using unit code properties
requires caution and a precise vision of the results of 
character set operations. In order to allow to user to
see results of character set operations, quex provides a query
mode where the character set corresponding to a specific property
setting can be investigated. Additionally, whole character set
expressions can be specified and quex displays the set of characters
that results from it.

In order to display the character set related to a unicode property
setting, call quex with the option ``--set-by-property`` followed 
by a string that specifies the setting in the same way as this is done in
regular expressions with the ``\P{...}`` operation. Note, that 
binary properties have no value in the sense that they are specified
in a manner as ``property-name=value``. Instead, it is sufficient to
give the name of the binary property and quex displays all characters
that have that property, e.g.

.. code-block:: bash

   > quex --set-by-property ASCII_Hex_Digit

displays all characters that have the property ``ASCII_Hex_Digit``, i.e.

.. code-block:: bash

    00020:                               0 1 2 3 4 5 6 7 8 9 
    00040: A B C D E F 
    00060: a b c d e f 

For non-binary properties the value of the property has to be specified.
For example, the set of characters where the property ``Block`` is
equal to ``Ethiopic`` can be displayed by calling

.. code-block:: bash

   > quex --set-by-property Block=Ethiopic

.. figure:: ../../figures/screenshot-block-ethiopic.*

Characters for unicode property ``Block=Ethiopic``.

and the result is displayed in figure <<fig-screenshot-block-ethiopic.png>>.
Naturally, sets specified with a simple property setting are not precisely
what the user desires. To apply complex operations of character set, quex
provides character set operations <<sec-formal/patterns/operations>>. Again,
it is essential to know which character sets these expressions expand. Thus,
quex provides a function to investigate set expressions with the
command line option ``--set-by-expression``. The following call

.. code-block:: bash

   > quex --set-by-expression 'intersection(\P{Script=Arabic}, \G{Nd})'

Displays all characters that are numeric digits in the arabic script. Note
that the display of characters on the screen is not always meaningful, so 
you might specify the one of the options:

.. describe:: --numeric 

   in order to display numeric values of the characters. 

.. describe:: --intervals 

   prints out character intervals instead of each isolated character. 

.. describe:: --names 

   which prints out the character names.

Depending on the specific information required, these options allow to display
the results appropriately.
