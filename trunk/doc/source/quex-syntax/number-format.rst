.. _sec-basics-number-format:

Number Format
=============

Numbers in Quex are specified in a way similar to what is common practice in
many programming languages such as C, Python, Java, etc. -- with some convenient
extensions. The number formats are presented in table :ref:`table:number-formats`.

 .. _table:number-formats:

 .. table:: Number formats

       +--------------+----------+---------------------------+
       | Type         | Prefix   | Example(s)                |
       +==============+==========+===========================+
       | Decimal      | none     | ``4711``                  |
       +--------------+----------+---------------------------+
       | Hexadecimal  | 0x       | ``0x8A5``, ``0xfe.43.a5`` |
       +--------------+----------+---------------------------+
       | Octal        | 0o       | ``0o721``                 |
       +--------------+----------+---------------------------+
       | Binary       | 0b       | ``0b0001.1010``           |
       +--------------+----------+---------------------------+
       | Roman        | 0r       | ``0rXMVIIII``, ``0rvii``  |
       +--------------+----------+---------------------------+
       | Napier       | 0n       | ``0nnaabdea``, ``0nABHJ`` |
       +--------------+----------+---------------------------+


Decimal integers do not start with '0' and have no prefixes.  Hexadecimal
numbers need to be preceded by '0x'. The dots inside the hexadecimal numbers
are meaningless for the parser, but may facilitate the reading for the human
reader.  Octal numbers are preceded by '0o'.  Binary numbers are preceded by
'0b'. Again, redundant dots may facilitate the human interpretation of the
specified number.  Roman numbers must be preceded by a '0r' prefix.  Napier
numbers (location arithmetic) must be preceded by a '0n' prefix.
