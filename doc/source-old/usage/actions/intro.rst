Actions
========

Once a pattern has been identified the caller of the lexical analyzer needs to
be notified about what the token was and may be what the lexeme was that
precisely matched. This type of *action* is the simplest kind of reaction to a
pattern match. The next section will focus on tokens can be easily send to the
caller of the lexical analyzer. More sophisticated actions may trigger the
transition to other modes. The shortcut definition for mode transition
triggering is explained in a dedicated section. Finally, actions may require
more code to be programmed. For this reason, it is discussed how C/C++ code can
be setup to perform actions.

Note, that actions not only occur as a companion of patterns. They may as well
be applied for incidences. Then they take the role of an incidence handler. The syntax,
though, for pattern-actions and actions for incidence handling is the same.

.. toctree::

   token-id-definition.txt
   sending-tokens.txt
   mode-transitions.txt
   c-actions.txt

