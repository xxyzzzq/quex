# (C) 2009-2011 Frank-Rene Schaefer
import quex.engine.generator.state.transition.core  as transition_block
import quex.engine.generator.state.entry            as entry_coder
from   quex.engine.generator.state.core             import input_do
from   quex.engine.generator.languages.address      import get_address
from   quex.engine.generator.languages.variable_db  import variable_db

from   quex.blackboard import setup as Setup, E_StateIndices
from   operator        import attrgetter

"""Template Compression _______________________________________________________

   Consider the file 'analyzer/mega_state/template/core.py' for a detailed 
   explanation of template compression.

   Code Generation ____________________________________________________________

   If there is a template consisting of a (adaptable) transition map such as 

                    [0, 32)    -> drop 
                    [32]       -> Target0  
                    [33, 64)   -> 721
                    [64, 103)  -> Target1
                    [103, 255) -> Target2

   where Target0, Target1, and Target2 are defined dependent on the involved
   states 4711, 2123, and 8912 as

                        4711   3123  8912
              Target0:   891   drop   213   
              Target1:   718   718    721
              Target2:   718   drop   711

   Then, the code generator need to create:

     (1) Transition Target Data Structures: 

             Target0 = { 891, 718, 718 };
             Target1 = {  -1, 718,  -1 };
             Target2 = { 213, 721, 711 };

         There might be multiple templates, so actually 'Target0' must be
         implemented as 'Template66_Target0' if the current template is '66'.
         The above writing is chosen for simplicity.

    (2) Templated State Entries:

            STATE_4711: 
               key = 0; goto TEMPLATE_STATE_111;
            STATE_3123: 
               key = 1; goto TEMPLATE_STATE_111;
            STATE_8912: 
               key = 2; goto TEMPLATE_STATE_111;

        this way the 'gotos' to templated states remain identical to the gotos
        of non-templated states. The 'key' lets the template behave according
        to a particular state.

    (3) Templated State (with its transition map, etc.):

            STATE_111: 
              input = get();

              if input in [0, 32)    then drop 
              if input in [32]       then Target0[key]  
              if input in [33, 64)   then 721          
              if input in [64, 103)  then Target1[key]
              if input in [103, 255) then Target2[key]

              ...

         The key is basically the index in the involved state list, e.g. '0' is
         the key for state '4711' above, '1' is the key for state '3123' and
         '2' is the key for '8912'.

    (4) State Router:
    
        A state router, all states in the target maps must be map-able if no
        computed goto is used.
        
            switch( state_index ) {
            case 4711: goto STATE_4711;
            case 3214: goto STATE_3214;
            ...
            }
"""

def framework(txt, TState, TheAnalyzer):
    input_do(txt, TState) 

def require_data(TState, TheAnalyzer):
    """Defines the transition targets for each involved state. Note, that recursion
       is handled as part of the general case, where all involved states target 
       a common door of the template state.
    """
    LanguageDB = Setup.language_db
    variable_db.require("state_key")

    def help(AdrList):
        return "".join(["{ "] + map(lambda adr: "QUEX_LABEL(%i), " % adr, AdrList) + [" }"])

    for target_scheme in sorted(TState.target_scheme_list, key=attrgetter("index")):
        assert len(target_scheme.scheme) == len(TState.state_index_list)
        def address(DoorId):
            if door_id == E_StateIndices.DROP_OUT:
                return get_address("$drop-out", TState.index, U=True, R=True)
            else:
                return LanguageDB.ADDRESS_BY_DOOR_ID(door_id)

        address_list = [ address(door_id) for door_id in target_scheme.scheme ]

        variable_db.require_array("template_%i_target_%i", 
                                  ElementN = len(TState.state_index_list), 
                                  Initial  = help(address_list),
                                  Index    = (TState.index, target_scheme.index))

    # Drop outs: all drop outs end up at the end of the transition map, where
    # it is routed via the state_key to the state's particular drop out.

