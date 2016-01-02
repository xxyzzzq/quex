.. _sec-encoding-queries:

Codec Queries
=============

The usage of encodings is facilitated with the following query options:

.. cmdoption:: `--encoding-info` [encoding-name]

   Displays the characters which are supported by the given encoding name.  If no
   encoding name is omitted, the list of all supported encodings is printed on the
   screen.

.. cmdoption:: `--encoding-file-info`  filename.dat

   Displays the characters that are covered by a user written encoding mapping 
   file.

.. cmdoption:: `--encoding-for-language` [language-name]

   Displays all supported encodings which are designed for the specified (human)
   language.  If no language's name is omitted, the list of all supported encodings
   is printed on the screen.

For example, if it is intended to design an input language for Chinese, quex
can be called to show the directly supported encodings (other than Unicode)::

    > quex --encoding-for-language

shows the list of supported languages::

    ...
    command line: English, Traditional Chinese, Hebrew, Western Europe, 
    command line: Greek, Baltic languages, Central and Eastern Europe, 
    command line: Bulgarian, Byelorussian, Macedonian, Russian, Serbian, 
    command line: Turkish, Portuguese, Icelandic, Canadian, Arabic, Danish, 
    command line: Norwegian, Thai, Japanese, Korean, Urdu, Vietnamese, 
    command line: Simplified Chinese, Unified Chinese, West Europe, Esperanto, 
    command line: Maltese, Nordic languages, Celtic languages, Ukrainian, 
    command line: Kazakh,

Now, asking for the encodings supporting the Celtic language::

    > quex --encoding-for-language 'Celtic languages'

delivers ``iso8859_14`` as possible encoding. Again a call to quex
allows to verify if all desired characters are supported. 

    > quex --encoding-info iso8859_14

By means of those queries it can be decided quickly which character encoding is
the most appropriate for ones needs. For some script and languages, though,
problems may arise from the fact that multiple code points carry the same
'character'. Systems that are able to render according to arabic letter
linking rules might rely on 28 unicode code points starting from 600 (hex).
The same 28 letters are represented in about 128 code points starting from
FE80 (hex)-for systems that might not be able to do the rendering automatically.

The decision which encoding to choose is very specific to the the particular
application. In any case, if ``iconv`` is installed on a system, the validity
of an encoding can be checked easily. One starts with some representive samples of the
text to be analyzed coded in UTF-8 (or any other 'complete' encoding). A call
to ``iconv`` of the type::

    > iconv -f utf-8 -t CodecX   sample.txt

shows the result on the screen. If there are characters which could not be
translated, then ``CodecX`` is not suited as an encoding to handle the file
``sample.txt``.


