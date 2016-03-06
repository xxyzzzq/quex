Incidence Handling
==================

User activity triggered by the lexical analyzer is not restricted to 'on
pattern match' as it is implemented by pattern-action pairs.  Instead, Quex
allows the definition of incidence handlers for several 'incidences'. 

.. note:: The term 'incidence' is chosen deliberately instead of 'event'. 
   The intend is to emphasize the difference to 'events' in state machines.
   An incidence is something 'big' that happened during analysis such as 
   a pattern match or the arrival at end-of-stream. Events in state machines
   are more 'atomic' in the sense that they trigger state transitions. Since
   Quex's business is closely related to state machines it had to be avoided
   to refer to two things with the same name. 

An incidence handlers can contain user written code which is executed as soon
as the particular incidence arrives. Examples for incidences are 'on_match' which is
triggered whenever a pattern matches, 'on_indentation' whenever there is a
transition from white space to non-white space after newline, and so on. Incidence
handlers are tied to modes, thus they are defined inside modes. An incidence
handler of a mode A is only armed as long as the lexical analyzer is in that
particular mode.

The following example shows how entry and exit of a mode may be used to 
send tokens that have been accumulated during analysis:

.. code-block:: cpp

    mode FORMAT_STRING { 
        ...
        on_entry { self.accumulator.clear(); }
        on_exit  { 
            self.accumulator.flush(QUEX_TKN_STRING); 
            self_send(QUEX_TKN_QUOTE);
        }
        ...
    }

The 'on_indentation' incidence handler may be used to create Python-like indentation
based languages--as shown in the following example:

.. code-block:: cpp

    mode PROGRAM {
        on_indentation {

            if( Indentation > self.indentation_stack.back() ) {
                ...
            }
            while( self.indentation_stack.back() > Indentation ) {
                self_send(QUEX_TKN_BLOCK_CLOSE);     
                self.indentation_stack.pop_back();
            }
            ...
        }

        {P_BACKSLASHED_NEWLINE} {
            self.disable_next_indentation_incidence();
        }
        ...
    }

The usage details about this example is explained in the sections to come.
