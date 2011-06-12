from quex.input.setup import setup as Setup

from collections import defaultdict
from copy        import copy, deepcopy
from operator    import attrgetter
from itertools   import ifilter
import sys

"""
Track Analysis

(C) 2011 Frank-Rene Schaefer
===============================================================================

The goal of track analysis is to profit from the static relations of 
states inside the state machine, so that the run-time effort can be 
reduced. At the end of the process, each state is decorated with a
set of attributes. They indicate how the state is to be implemented 
as source code.

The implementation of the state has the following basic elements:

*-----------------------------------------------------------------------------*

   Input:           Access the input character.

   SuccessorInfo:   [OPTIONAL] Store information to be used by successor states.

   TriggerMap:      All triggers that transit on a character to specific 
                    successor state.

   DropOut:         Handle the case that input character does not trigger in
                    trigger map.

*-----------------------------------------------------------------------------*

Accordingly, each state will be represented by a new 'state' consisting
of four objects:

    .input          <-- class Input
    .successor_info <-- class SuccessorInfo
    .trigger_map    <-- list of pairs (interval, target_state_index)
    .drop_out       <-- class DropOut

The following sections elaborate on the these objects and how they have
to perform. The classes 'Input', 'SuccessorInfo' and 'DropOut' allow
to access the information that resulted from the track analyzis. After
reading the following, review their class interfaces.
_____________________
                     |
Acceptance Detection |__________________________________________________________
---------------------'

The following discussion shows how these elements are configured. Consider
the simple state machine:

      ( 1 )-- 'a' -->( 2 )-- 'b' -->(( 3 ))
                                          "ab"

Is says that state 1 transits on 'a' to state 2. State 2 transits on 'b'
to state 3. State 3 is an acceptance state that indicates that pattern "ab" 
has been matched. This state machine can be implemented as follows:

        State1:
            /* Input */            input = *input_p;   
            /* TransitionBlock */  if( input == 'a' ) goto State2;
            /* DropOut */          goto Failure;

        State2:
            /* Input */            ++input_p;
                                   input = *input_p;   
            /* TransitionBlock */  if( input == 'b' ) goto State3;
            /* DropOut */          goto Failure;

        State2:
            /* Input */            ++input_p;
            /* DropOut */          goto Terminal('ab');

The following rules can already be derived:

*-----------------------------------------------------------------------------*

  Input:   (1) The init state does not increment the input_p,

           (2) If the state is the terminal of a post-context pattern
               without further transitions, then the input position
               is set to the end of the core pattern. Thus, it does
               not need to be incremented.

           (3) All other states increment/decrement the input position.

  DropOut: 
           (3) if no pattern ever matched the drop-out must be 'goto Failure'.

           (4) if the state is an acceptance state, then the drop-out must
               be 'goto Terminal;' where 'Terminal' is the address of the 
               action code that relates to the matching pattern.

  General: (5) When a terminal is reached, the input **must** point to the
               next character to be analyzed, i.e. one after the last
               character that matched!
*-----------------------------------------------------------------------------*

A somewhat more complicated state machine may be the following:

    ( 1 )-- 'a' -->(( 2 ))-- 'b' -->( 3 )-- 'c' -->(( 4 ))
                         "a"                             "abc"

Here, state 2 looks different since it is an acceptance state and contains a
transition on 'b' to state 3. However, with the above rules it still behaves as
expected. If something different from 'b' arrives, then the input pointer
stands on the position right after the matched character 'a' and we transit to
the terminal of pattern "a". 

State 3 is interesting. If no 'c' is detected then, still, pattern "a" has
matched already. So, state 3 can actually goto Terminal("a"), but the input
position must be decreased by 1 so that it points directly behind the matched
character "a". A new rule can be stated about the DropOut:

*-----------------------------------------------------------------------------*

   DropOut: (6) If a state itself is not an acceptance state, but some
                state before it is an acceptance state, then 
               
                  (6.1) set the input pointer back to the position 
                        where the last acceptance state matched.
                  (6.2) goto the terminal of the last acceptance
                        state.

*-----------------------------------------------------------------------------*

In the case above, the resetting of the input pointer is trivial. Now, 
consider the state machine
                                     'd'
                                    ,---.
                                    \   /
    ( 1 )-- 'a' -->(( 2 ))-- 'b' -->( 3 )-- 'c' -->(( 4 ))
                         "a"                             "abc"

Now, an arbitrary number of 'd's may occur before state 3 drops out.  This
requires, that state 2 must store the acceptance position and state 3 must
reset the acceptance position from a variable. Two new rules:

*-----------------------------------------------------------------------------*

  SuccessorInfo: (7) If there is a non-acceptance successor state 
                     that is reached via a path of arbitrary length 
                     (i.e. there is a loop somewhere), then the 
                     acceptance position must be stored in a variable
                     'last_acceptance_position'.

  DropOut: (8.1) For a non-acceptance state; If the path from the last 
                 acceptance state to this state is of arbitrary length, 
                 then the input position must be set to what 
                 'last_acceptance_position' indicated.

           (8.2) The same is true, if the state can be reached by multiple
                 acceptance states that have a different distance to this 
                 state.

*-----------------------------------------------------------------------------*

An even more complicated case may be mentioned here:

    ( 1 )-- 'a' -->(( 5 ))-- 'b' ---.
       \                 "a|abc"     \
        \                             \
         `-- 'b' -->(( 2 ))-- 'b' -->( 3 )-- 'c' -->(( 4 ))
                          "b"                             "a|abc"

The pattern "a|abc" wins in state 5 and state 4. Pattern "b" wins in state 2.
Now, it cannot be said upfront what pattern has matched if state 3 is reached.
Thus, the acceptance state must store information about the acceptance:

*-----------------------------------------------------------------------------*

    SuccessorInfo: (9) If there is a non-acceptance successor that
                       can be reached from different acceptance states,
                       then the state must store the information about
                       the acceptance in a variable 'last_acceptance'.

    DropOut: (10) For non-acceptance state; If the state can be reached
                  by different acceptance states, or if there are preceding 
                  acceptance states and a path without acceptance, then the 
                  terminal store in 'last_acceptance' must be entered.

*-----------------------------------------------------------------------------*

_____________________
                     |
Pre-Contexts         |__________________________________________________________
---------------------'

Note, that 'Acceptance' may be dependent on pre-contexts, that is the
acceptance of a state generally is determined by a sequence of checks:

    if     ( pre_context[...] ) acceptance X
    else if( pre_context[...] ) acceptance Y
    else                        acceptance Z

where X has higher priority than Y and Y has higher priority than Z. Z is the
highest priority pattern without pre-context. All pre-context dependent
acceptance states are neglected because they are dominated by Z. 

DEFINITION 'acceptance info': Let such a sequence of checks be defined as 
                              the 'acceptance info' of a state.

Pre-context flags, however, are constant as soon as the forward lexical
analysis starts. Any combination of pre_contexts being fulfilled is
conceivable-including no pre-context. If two states have a different acceptance
info, then this means that there is a combination of pre-contexts were they
have a different acceptance. Thus the condition 'different acceptance' from the
rules above can be generalized to 'different acceptance info'. The comparison
of two acceptance chains is enough to judge whether the acceptance of two
states is equivalent.

Now, consider the state machine:

      ( 1 )-- 'a' -->( 2 )-- 'b' -->( 3 )-- 'c' -->(( 4 ))
                                                         "xyz/abc/"

which means that pattern "abc" must be preceded by pattern "xyz" in order to
match. All successor acceptance states of state 1, though, depend on the
pre-context "xyz". Thus, state 1 could actually drop-out immediately if the
pre-context is not met. It is not necessary to transit through states 2, 3, and
4 to find out finally, that pattern "xyz/abc/" fails because of the
pre-context. A new rule can be defined

*-----------------------------------------------------------------------------*

   SuccessorInfo: (11) If all successor acceptance states depend on 
                       a certain pre-context flag being raised, then
                       the first state on that path can drop-out 
                       on the condition that the pre-context is not met.

   Terminal:      (12) When a terminal is reached where the pathes took 
                       care of the pre-context checks, then there is no
                       need to check it again in the terminal.

*-----------------------------------------------------------------------------*

_____________________
                     |
Post-Contexts        |__________________________________________________________
---------------------'

Post contexts are patterns that must be present after the core pattern.  When
the end of the post-context matches, then end of the lexeme must be set to the
end of the core pattern. Example:


      ( 1 )-- 'a' -->( 2 )-- 'b' -->( 3 )-- ':' -->(( 4 ))
                                      S("abc")           "abc/:"

That is pattern "abc" must be followed by ":". After the match, though, the
analysis starts with ':' not with what comes after it. If a post-contexted
patten is matched the position of the end of the core pattern must be 
restored. Similar to the acceptance discussion about new rules can 
be introduced:

*-----------------------------------------------------------------------------*

   SuccessorInfo: (13) If the length of the path from the end-of-core-pattern
                       to the final end-of-post context is arbitrary (due to
                       loops), then the input position of the end-of-core
                       pattern must be stored in a variable 'post_context_position[i]'.

   DropOut: (14) If the match is the end of a post context, then the position
                 of the core pattern needs to be restored.

               (14.1) If the distance to the end of the core pattern can be 
                      determined statically, then the input position is decremented
                      accordingly.

               (14.2) Else, the input position must be set to what is indicated
                      by variable 'post_context_position[i]'.
               
*-----------------------------------------------------------------------------*

Note, that it is not necessary to store what core pattern has matched, since
the fact that the end of the core pattern has been reached testifies what
core pattern is passed. Further, if there are multiple post-context
with the same core-patterns, then the 'post_context_position' can be shared,
if is stored in exactly the same states.

*-----------------------------------------------------------------------------*

    General: (15) post-constext that store their input positions in exactly
                  the same states can share their post_context_position 
                  variable.

*-----------------------------------------------------------------------------*

_____________________
                     |
Lexeme Start Pointer |__________________________________________________________
---------------------'

[[ This needs some clarification: What happens, if no acceptance state is
   reached then? OnFailure would expect that the input position is 
   lexeme_start_p + 1. This is impossible if it is reset at reload.
]]

On reload, in general, the current lexeme must be maintained so that is 
can be accessed in the pattern-action. However, if for a state it 
can be determined that no successor acceptance state cares about the lexeme,
then the lexeme start pointer can be set to the current input position. 
This allows to quickly skip large 'comment' section that span regions that
are even bigger than the current input buffer size. 

A new rule concerning the reload behavior can be defined:

    OnReload:

    (16) If no successor acceptance state 'cares' about the lexeme and
         a 'dont-care' acceptance state has been passed, then then reload
         can set the lexeme_start_p to the current input position and 
         reload the buffer from start.

    (17) All non-acceptance states that immediately follow a 'skipper
         state' must cause 'skip-failure' on drop-out.
"""
def do(SM, ForwardF):
    """Determines a database of AcceptanceTrace lists for each state.
    """
    return TrackInfo(SM, ForwardF).acceptance_trace_db

class TrackInfo:
    def __init__(self, SM, ForwardF):
        """SM -- state machine to be investigated."""
        assert type(ForwardF) == bool
        self.sm          = SM
        self.__forward_f = ForwardF

        # (1) Analyze recursively in the state machine:
        #
        # -- 'Loop States'.
        #    Collect states that are part of a loop in the state machine.  If a
        #    path from state A to state B contains one of those states, then the
        #    number of transitions that appear between A and B can only be
        #    determined at run-time.
        #
        #    set of state indices that are part of a loop.
        #
        self.loop_state_set = set([])
        #    NOTE: The investigation about loop states must be done **before**
        #          the analysis of the acceptance traces. The acceptance trace
        #          analysis requires the loop state set to be complete!
        self. __loop_state_search(self.sm.init_state_index, [])

        # -- Database of Passed Acceptance States
        # 
        #    map:  state_index  --> list of AcceptanceTrace objects.
        #
        self.acceptance_trace_db = dict([(i, []) for i in self.sm.states.iterkeys()])
        self.__acceptance_trace_search(self.sm.init_state_index, 
                                       path             = [], 
                                       acceptance_trace = AcceptanceTrace())

    def __loop_state_search(self, StateIndex, path):
        """Determine the indices of states that are part of a loop. Whenever
           such a state appears in a path from one state A to another state B, 
           then the number of transitions from A to B cannot be determined 
           from the state machine itself.

           Recursion Terminal: When a state has no target state that has not
                               yet been handled in the path. This is implemented
                               int the loop itself.
        """
        # if StateIndex in path: return

        # (1) Add current state index to path
        path.append(StateIndex)

        state = self.sm.states[StateIndex]

        # (2) Iterate over all target states
        for state_index in state.transitions().get_target_state_index_list():
            if state_index in path: 
                # Mark all states that are part of a loop. The length of a path that 
                # contains such a state can only be determined at run-time.
                idx = path.index(StateIndex)
                self.loop_state_set.update(path[idx:])
                continue # Do not dive into done states

            self.__loop_state_search(state_index, path)

        # (3) Remove current state index --> path is as before
        x = path.pop()
        assert x == StateIndex

    def __acceptance_trace_search(self, StateIndex, path, acceptance_trace):
        """StateIndex -- current state
           path       -- path from init state to current state (state index list)

           last_acceptance_i -- index in 'path' of the last acceptance state. 
                                path[last_acceptance_i] == state index of 
                                last acceptance state.

           last_post_context_i_db[k] -- index in 'path' of the last state where post context 
                                        'k' begins. 
                                        path[last_post_context_i_db[k] == state index 
                                        of last state where post context k begins.

           Recursion Terminal: When state has no target state that has not yet been
                               handled in the 'path'.
        """
        # (1) Add current state to path
        path.append(StateIndex)

        ## print "## ----------------"
        # (2) Update the information about the 'trace of acceptances'
        acceptance_trace.update(self, path) 

        # (3) Mark the current state with its acceptance trace
        #     NOTE: When this function is called, acceptance_trace is already
        #           an independent object, i.e. constructed or deepcopy()-ed.
        ## print "## ", StateIndex
        ## print "## ", path
        ## print "## ", acceptance_trace
        self.acceptance_trace_db[StateIndex].append(acceptance_trace)

        # (4) Recurse to all (undone) target states. 
        for target_index in self.sm.states[StateIndex].transitions().get_target_state_index_list():
            # Do not dive into done states / prevents recursion along loops.
            if target_index in path: continue 
            self.__acceptance_trace_search(target_index, path, deepcopy(acceptance_trace))

        # (5) Remove current state index --> path is as before
        x = path.pop()
        assert x == StateIndex

class AcceptanceTrace:
    """For one particular STATE that is reached via one particular PATH 
       an AcceptanceTrace accumulates information about what pattern 'ACCEPTS'
       and where the INPUT POSITION is to be placed.

       This behavior may depend on pre-contexts being fulfilled.

       In other words, an AcceptanceTrace of a state provides information
       about what pattern would be accepted and what the input positioning
       should be if the current path was the only path to the state.

       The acceptance information is **priorized**. That means, that it is
       important in what order the pre-contexts are checked. 

       Example:

       ( 0 )----->(( 1 ))----->( 2 )----->(( 3 ))----->( 4 )------>( 5 ) ....
                   8 wins                 pre 4 -> 5 wins                    
                                          pre 3 -> 7 wins

       AcceptanceTrace-s for each state:

       State 0: has no acceptance trace, only '(no pre-context, failure)'.
       State 1: (pattern 8 wins, input position = current)
       State 2: (pattern 8 wins, input position = current - 1)
       State 3: (if pre context 4 fulfilled: 5 wins, input position = current)
                (if pre context 3 fulfilled: 7 wins, input position = current)
                (else,                       8 wins, input position = current - 2)
       State 4: (if pre context 4 fulfilled: 5 wins, input position = current - 1)
                (if pre context 3 fulfilled: 7 wins, input position = current - 1)
                (else,                       8 wins, input position = current - 3)
       ...
    """
    def __init__(self):
        self.__sequence = { 
            None: AcceptanceTraceEntry(PreContextID                 = None, 
                                       PatternID                    = -1, # Failure
                                       TransitionN_ToAcceptance     = 0,
                                       AcceptingStateIndex          = -1, # Init State
                                       TransitionN_SincePositioning = -1, # input_p = lexeme_start_p + 1
                                       PositioningStateIndex        = -1, 
                                       PostContextID                = -1),
        }
        self.__last_transition_n_to_acceptance = 0

    def __len__(self):
        return len(self.__sequence)

    def update(self, track_info, Path):
        # It is essential for a meaningful accumulation of the match information
        # that the entries are accumulated from the begin of a path towards its 
        # end. Otherwise, the 'longest match' cannot be applied by overwriting
        # existing entries.
        assert abs(self.__last_transition_n_to_acceptance) < len(Path)
        self.__last_transition_n_to_acceptance = len(Path)

        # If the current state is a loop state, than all positions become void.
        # This means that number of characters to reach this state can no longer
        # be determined by the state machine structure itself.
        StateIndex = Path[-1]

        ## print "##StateIndex", StateIndex
        if StateIndex in track_info.loop_state_set:
            # If there is a loop, then the number of transitions from one state to the
            # other may be not be determined from the state machine structure.
            for entry in self.__sequence.itervalues():
                ## print "##entry:", entry
                # -1  means 'lexeme_start_p + 1' so we would not 'voidify' it
                if entry.transition_n_since_positioning != - 1:
                    entry.transition_n_since_positioning = None
        else:
            # Add '1' to the distance between:
            #       positioning state --> transition_n_since_positioning
            for entry in self.__sequence.itervalues():
                if entry.transition_n_since_positioning != -1 and entry.transition_n_since_positioning is not None:
                    entry.transition_n_since_positioning += 1

        state = track_info.sm.states[StateIndex]
        if not state.is_acceptance(): return

        # (*) An unconditional acceptance deletes all previous influence 
        #     from past traces.
        for dummy in ifilter(lambda origin:     origin.is_acceptance() 
                                            and origin.pre_context_begin_of_line_f() == False
                                            and origin.pre_context_id() == -1,
                             state.origins()):
            self.__sequence.clear()
            # The 'None' case which must always be there is now setup ...

        L = len(Path)
        for origin in sorted(state.origins(), key=attrgetter("state_machine_id")):
            if not origin.is_acceptance(): continue

            # (0) The pattern's ID and its pre-context
            pattern_id     = origin.state_machine_id
            pre_context_id = extract_pre_context_id(origin)
            
            ## print "##", StateIndex, pattern_id, pre_context_id
            # (2) The position where the input pointer has to be set if the 
            #     pattern is accepted (how many characters to go backwards).
            if origin.post_context_id() == -1: 
                post_context_id                = -1
                transition_n_since_positioning = 0
                positioning_state_index        = StateIndex
            else:
                post_context_id = origin.post_context_id()
                transition_n_since_positioning,        \
                positioning_state_index = self.__find_last_post_context_begin(origin.post_context_id(), 
                                                                              Path, 
                                                                              track_info)

            if track_info.loop_state_set.isdisjoint(Path):
                transition_n_since_init_state = L
            else:
                # If there is a loop somewhere connected to the path, then the distance to
                # the current state can only be determined as 'at least' == path length.
                # N < 0 shall mean: 'at least' N characters
                transition_n_since_init_state = - L
            
            # (*) Make the entry in the database
            entry = AcceptanceTraceEntry(pre_context_id, pattern_id, 
                                         TransitionN_ToAcceptance     = transition_n_since_init_state,
                                         AcceptingStateIndex          = StateIndex, 
                                         TransitionN_SincePositioning = transition_n_since_positioning,
                                         PositioningStateIndex        = positioning_state_index, 
                                         PostContextID                = post_context_id)

            # (*) IMPORTANT: What is happening here is a simple **overwriting**
            #                of existing entries, but this works only if the path
            #                is transversed from begin to end. Then this implements 
            #                implicitly **longest match**, i.e. latest wins.
            self.__sequence[pre_context_id] = entry

            # The rest of the traces is dominated
            if pre_context_id is None: break

        ## print "##1", StateIndex, L, self.__sequence
        #min_pattern_id = self.__sequence[None].pattern_id
        #if min_pattern_id != -1:
        #    # -- No conditional pattern can ever be matched if it is dominated
        #   #    by an unconditional pattern acceptance.
        #    # -- But, the current state's acceptances can never be deleted.
        #    #    thus check this before adding current state's info.
        #    for key, dummy in ifilter(lambda x:     (x[1].pattern_id > min_pattern_id)
        #                                        and abs(x[1].transition_n_to_acceptance) != L, 
        #                              self.__sequence.items()):  # NOT: iteritems() here!
        #        del self.__sequence[key]
        ## print "##1", StateIndex, self.__sequence

        # Assume that the last entry is always the 'default' where no pre-context is required.
        assert len(self.__sequence) >= 1
    
    def __getitem__(self, PreContextID):
        return self.__sequence[PreContextID]

    def get(self, PreContextID):
        return self.__sequence.get(PreContextID)

    def get_priorized_list(self):
        def my_key(X):
            # Failure always sorts to the bottom ...
            if X[1].pattern_id == -1: return (sys.maxint, sys.maxint)
            # Longest pattern sort on top
            # Lowest pattern ids sort on top
            return (- X[1].transition_n_to_acceptance, X[1].pattern_id)

        result = self.__sequence.items()
        result.sort(key=my_key)
        return result

    def get_priorized_pre_context_id_list(self):
        return map(lambda x: x[0], self.get_priorized_list())

    def __repr__(self):
        txt = []
        for x in self.__sequence.itervalues():
            txt.append(repr(x))
        return "".join(txt)

    def __eq__(self, Other):
        return None

    def __find_last_post_context_begin(self, PostContextID, Path, track_info):
        """Walk the path backwards until the state is found that stores the position
           of the acceptance.
        """
        distance = 0
        successor_is_loop_state_f = (Path[-1] in track_info.loop_state_set)
        for state_index in reversed(Path[:-1]):
            if distance is not None: distance += 1

            if successor_is_loop_state_f:
                # If the state is part of a loop, then the distance backwards cannot be 
                # determined from the structure of the state machine.
                distance = None

            for origin in track_info.sm.states[state_index].origins():
                if     origin.post_context_id() == PostContextID \
                   and origin.store_input_position_f(): 
                    return distance, state_index

            successor_is_loop_state_f = (state_index in track_info.loop_state_set) 
        
        # This function is only to be called to find the beginning of a post context. It
        # **must** be impossible to reach a post-context end without passing the place where
        # the post context begins. Thus, the path **must** contain a state that stores this
        # position. If we reach this position here, then something is seriously wrong. 
        assert False

    def __iter__(self):
        for x in self.__sequence.itervalues():
            yield x

class AcceptanceTraceEntry(object):
    __slots__ = ("pre_context_id", 
                 "pattern_id", 
                 "transition_n_since_positioning", 
                 "transition_n_to_acceptance", 
                 "accepting_state_index", 
                 "positioning_state_index",
                 "post_context_id")

    def __init__(self, PreContextID, PatternID, 
                 TransitionN_ToAcceptance, 
                 AcceptingStateIndex, 
                 TransitionN_SincePositioning, 
                 PositioningStateIndex, 
                 PostContextID):
        """PreContextID  --
           PatternID     -- 
           TransitionN_SincePositioning -- Number of transitions since the 'positioning'
                                           state has been reached.
           AcceptingStateIndex -- Index of the state that accepts the mentioned
                                  pattern. This is used when we need to inform
                                  the state that it needs to store the acceptance
                                  information.
           PositioningStateIndex -- Index of the state that positions the input pointer
                                    in the case of acceptance. This is usually the 
                                    acceptance state. For post-context patterns it is 
                                    the state where the post context begins.

           PostContextID   = -1  acceptance has nothing to do with post context
                          != -1  acceptance is related to post context with given id.
        """
        self.pre_context_id  = PreContextID
        self.pattern_id      = PatternID
        self.transition_n_since_positioning = TransitionN_SincePositioning
        # Transitions To Acceptance 
        # 
        # This basically means how many transitions happened since the init
        # state when the pattern was accepted. For non-post-context patterns
        # this is the lexeme length; For post-context patterns this is the 
        # length of the core pattern plus the length of the post context.
        #
        #  N >= 0 :   distance(init state, acceptance) == exactly 'N' characters
        #  N <  0 :   distance(init state, acceptance) >= 'N' characters
        self.transition_n_to_acceptance = TransitionN_ToAcceptance

        # 
        self.accepting_state_index   = AcceptingStateIndex
        self.positioning_state_index = PositioningStateIndex
        #
        self.post_context_id         = PostContextID

    def __repr__(self):
        txt = ["---\n"]
        txt.append("    .pre_context_id                 = %s\n" % repr(self.pre_context_id))
        txt.append("    .pattern_id                     = %s\n" % repr(self.pattern_id))
        txt.append("    .transition_n_since_positioning = %s\n" % repr(self.transition_n_since_positioning))
        txt.append("    .transition_n_to_acceptance     = %s\n" % repr(self.transition_n_to_acceptance))
        txt.append("    .accepting_state_index          = %s\n" % repr(self.accepting_state_index))
        txt.append("    .positioning_state_index        = %s\n" % repr(self.positioning_state_index))
        txt.append("    .post_context_id                = %s\n" % repr(self.post_context_id))
        return "".join(txt)

AcceptanceTraceEntry_Void = AcceptanceTraceEntry(PreContextID                 = None, 
                                                 PatternID                    = None, # Undetermined
                                                 TransitionN_ToAcceptance     = 0,
                                                 AcceptingStateIndex          = -1, 
                                                 TransitionN_SincePositioning = None, # Undetermined
                                                 PositioningStateIndex        = -1, 
                                                 PostContextID                = -1)

def extract_pre_context_id(Origin):
    """This function basically describes how pre-context-ids and 
       'begin-of-line' pre-context are expressed by an integer.
    """
    if   Origin.pre_context_begin_of_line_f(): return -1
    elif Origin.pre_context_id() == -1:        return None
    else:                                      return Origin.pre_context_id()

