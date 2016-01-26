Pitfalls
=========

Behavior may surprise. Good behavior introduce a note of levity; but bad
behavior impose cautious reconsideration. This holds for any type of behavior
and in particular for the behavior of a generated lexical analyzer. Some causes
emerge quickly under the light of the documentation. Other behavior remains
obscure without a thorough investigation. This section elaborates on pitfalls,
i.e. causes for negatively surprising behavior. The first part discusses
pitfalls on pattern matching and the second part discusses pitfalls on
incidence handling.  A final section deals with a deficiency inherent to
state-machine-based lexical analyzers: the *dangerous trailing context*
:cite:`Paxson2007lexical`. It is explained how this problem is partly solved.

.. toctree::

    pattern-matching.rst
    incidence-handler.rst
    defficiency.rst
