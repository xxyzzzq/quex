Unicode Properties
==================

The first doubt that arises when properties are to be applied is whether the
properties actually exists. The second doubt, then, is what values these
properties can actually have. To help out with the first question, simply call
quex with the command line option ``--property`` and it prints a list of
properties that it is able to extract from the unicode database. This
leads to an output as follows:

.. code-block:: bash

    # Abbreviation, Name, Type
    AHex,    ASCII_Hex_Digit,                    Binary
    Alpha,   Alphabetic,                         Binary
    Bidi_C,  Bidi_Control,                       Binary
    Bidi_M,  Bidi_Mirrored,                      Binary
    CE,      Composition_Exclusion,              Binary
    Comp_Ex, Full_Composition_Exclusion,         Binary
    DI,      Default_Ignorable_Code_Point,       Binary
    Dash,    Dash,                               Binary
    Dep,     Deprecated,                         Binary

    ...

    na,      Name,                               Miscellaneous
    na1,     Unicode_1_Name,                     Miscellaneous
    nt,      Numeric_Type,                       Enumerated
    nv,      Numeric_Value,                      Numeric
    sc,      Script,                             Catalog
    scc,     Special_Case_Condition,             String,        <unsupported>
    sfc,     Simple_Case_Folding,                String,        <unsupported>
    slc,     Simple_Lowercase_Mapping,           String,        <unsupported>
    stc,     Simple_Titlecase_Mapping,           String,        <unsupported>
    suc,     Simple_Uppercase_Mapping,           String,        <unsupported>
    tc,      Titlecase_Mapping,                  String,        <unsupported>
    uc,      Uppercase_Mapping,                  String,        <unsupported>

Each line contains three fields separated by commas. The first field contains
the *alias* for the property name, the second field contains the *property name*,
and the last column contains the *type* of property. If a field containing
``<unsupported>`` is appended, this means that this property is not supported
by quex. In most cases this so because these properties support character operations
rather then the definition of character sets. 

To help out with the second question call quex with the command line option
``--property`` followed by the name of the property that you want to know more about. The following displays the query about the property ``Numeric_Type``:

.. code-block:: bash

    > quex --property Numeric_Type
    (please, wait for database parsing to complete)

    NAME          = 'Numeric_Type'
    ALIAS         = 'nt'
    TYPE          = 'Enumerated'
    VALUE_ALIASES = {
            Decimal(De),
            Digit(Di),
            Numeric(Nu).
    }

This tells, that ``Numeric_Type`` is a property of type ``Enumerated``, i.e. its
values are taken from a fixed list of values. The *alias* ``nt`` can be used as a
placeholder for ``Numeric_Type``, and the possible value settings are ``Decimal``,
``Digit``, and ``Numeric``. The strings mentioned in parenthesis are the *value aliases*
that can be used as placeholders for the values, in case one does not want to type
the whole name of the value. From this output one knows that expressions
such as ``\P{Numeric_Type=Decimal}``, ``\P{nt=Di}``, and ``\P{Numeric_Type=Nu}`` are
valid for this property. The next doubt that arises is about the character set
that is actually spanned by such expressions. This is discussed in the subsequent
section.
