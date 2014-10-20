Action Reduction/Action Postponing

(C) Frank-Rene Schaefer
-------------------------------------------------------------------------------
ABSTRACT:

This file describes the theoretical background for the process applied by Quex
used to reduce the number of actions or to postpone actions. Any write action
that can be avoided during state transitions may bring a strong performance
increase (due to avoided cache misses, for example). Every action is preferred
to be postponed, because earlier states are passed more often than later
states.

-------------------------------------------------------------------------------
SITUATION:

This document provides the groundwork for algorithms that optimize state
machines by means of reductions of transition actions. It defines precise terms
for further discussions.

Incoming characters cause state transitions. Transitions are adorned with
operations, such as 'store last acceptance'. At some point, an incoming
character does not fit a transition map of the current state and the state
machine exits.  Upon exit, some consequences are derived  based on the passed
operations and the current state. The steps in the run through a state machine
are depicted in figure 1.


                         .----------<---------------.
                         |                          |
               Begin -------> Operations -----> Transitions -----> Exit
                                                       

           Figure 1: The run through a state machine

Each phenomenon can be associated with a set of variables by which it is
determined. The line and column numbers are determined by the current line and
column number and the previous line and current number, for example. The sets
of variables which are associated with an investigated procedure, is called
SOV.

DEFINITION: SOV -- Set of Variables

    The term 'set of variables' SOV shall stand for the set of all
    variables which are relevant to the investigated behavior. 

The variables of an SOV evolve along state transitions. Not all variables may
be necessary in all states. For example, if the lexeme length is not required
in a terminal, then no state on the path to the terminal is required to
contribute to the development of that variable. Let the state specific 
set of variables SOV(i) be defined.

DEFINITION: SOV(i) -- The state specific required set of variables.

    The set of variables SOV(i) in state 'i' contains all variables which are
    required to satisfy the requirements of all successor states of state 'i'.

As a direct consequence, the 'SOV(i)' for each state can be determined by
*back-propagation* of needs. A state or terminal which requires a specific
variable tags all of its predecessor states with this requirement. That is, if
a state 'k' requires a variable 'x' than 'x is element of SOV(i)' for all 'i'
in the set of states that lead to 'k'.

A state machine changes variables of the SOV. These changes are consequences of
operations that happen upon entry into states. Let an 'operation' be defined as
follows.

DEFINITION: op(i) -- Operation 

    The modification on the SOV upon entry into a state 'i' is called an
    operation 'op(i)'. With 'x' as the setting of the SOV before entry
    into a state 'i' the term, the setting of the SOV in state 'i' becomes

                         SOV(i) = op(i)(x)

That is, 'op(i)' is a function or a procedure that is applied on the set of
variables of concern. All investigated behavior along the state machine 
concentrates on operations on the SOV.

-------------------------------------------------------------------------------

LINEAR STATES AND MOUTH STATES:

Two central concept of the analysis algorithms are 'linear states' and 'mouth
states' as they are defined in the paragraphs to follow. They differ in the way
how actions that happen before influence the SOV behind them.

DEFINITION: Linear State

    A linear state is a state that is entered only through one predecessor 
    state, i.e. it has only one entry.

                                    .---> ...
                                   /
                        ... --->( 0 )---> ...

                Figure 1: The concept of a linear state.

Since there is only one predecessor state to a linear state the SOV can be
derived from the SOV at the predecessor and the operation at the entry of the
linear state itself. Let 'p(i)' denote the predecessor state of 'i'. Then,

                 SOV(i) = op(i)(SOV(p(i)))

if 'p(i)' is also a linear state, then the right hand of the above equation can
be expanded

                 SOV(i) = op(i)(SOV(op(p(i))(SOV(p(p(i))))))

Let OP(i,k) denote the concatinated operations from state 'k' to state 'i'
along a sequence of linear states, then SOV(i) can be determined by the SOV(k)
through

                 SOV(i) = OP(i,k)(SOV(k))

That is, if SOV(k) is determined, then SOV(i) can be determined without the
operations along the path from 'k' to 'i', but in the state 'i' itself. 
Figure 2 displays an example, that shows how this can be used to reduce 
computational effort. 

                     x=x+1       x=x+1       x=x+1        
           ... ( a )------>( b )------>( c )------>( d )------>


             Figure 2: A string of linear states

For an exit in state 'd' the actions can be described in general terms as

       SOV(b) = (op, b) on SOV(a)
       SOV(c) = (op, c) on SOV(b)
       SOV(d) = (op, d) on SOV(c)
       SOV(e) = (op, e) on SOV(d)
              = (op, e) on ((op, d) on ((op, c) on ((op, b) on SOV(a))))
                 
The SOV in figure 2 is 'x' and the action in figure 2 is 'x = x + 1'. Thus,
with 'x(i)' as the 'x' in state 'i' the sequence in the becomes:
    
                          x(b) = x(a) + 1
                          x(c) = x(b) + 1
                          x(d) = x(c) + 1
                          x(e) = x(d) + 1
                         
Or, shortly              
                         
                          x(e) = x(a) + 4
       
The formula for 'x(e)' can be considered as a recipe to determine the SOV in a
state, without knowing the previous operations along the path.  In the example
above, a longer sequence of additions was transformed into a single addition.
Let the term recipe be define for the context of this discussion.

DEFINITION: R(i) -- Recipe 

   A recipe 'R(i)' for a state 'i' is a description of how to determine 
   the SOV(i) when the state has been entered. It maps

                     (s, r, c) ---> SOV(i)

   where 's' is the current state including his variables. 'r' is a setting of
   registers that store temporary data, and 'c' is a set of constants. 

Along a sequence of linear states, there is an obvious relation between a
recipe an the concatinated operations

                   SOV(i) = OP(i,x)(SOV(x))

If 'i' is reached from 'x' by a sequence of linear states, then the SOV(x) and
the OP(i,x) build together the recipe R(i). 'SOV(i)' is an example of content
stored in registers, i.e. the 'r' in the definition of a recipe. An example for
constants 'c' can be observed in the example from figure 2, where 'x' was computed
as the content of 'x' stored 'a' plus a constant number. 

An example for a state variable in a recipe would be, for example, the
computation of the lexeme length 'lengh(i)' based on the distance to the
position of first character 'p0'. Let 'ip' be the pointer to the position where
the current character is located. Then the lexeme length can be expressed as

                        length(i) = (ip - p(a))

and 'ip' is a state variable, i.e. an element of 's' from the definition of 
a recipe. The iterative development of recipies can only start at a state
where either the recipe to compute the SOV is determined. Only then, any 
previous history can be dropped from consideration, because it is reflected
in the state's recipe.

DEFINITION: Spring

    A spring is a state where a walk along linear states can begin. For a state
    'i' to act as a spring, the recipe 'R(i)' must be determined.

If the spring is connected to a linear state, then this linear state can
determine its recipe through concatenation, as discussed earlier. Let this
process of iterative concatenation be called accumulation.

DEFINITION: Accumulation

    The process of determining a recipe of a linear state base on the recipe
    of a predecessor state is called 'accumulation'.

If a linear state that received a recipe through accumulation can now itself
act as a basis for accumulation for successor linear states. This process can
be repeated until a mouth state is reached.  Mouth states are the counterpart
to linear states. 

DEFINITION: Mouth State

    A mouth state is a state that is entered from more than one state. An 
    example is depicted in figure 1.

                        ... --->--.   .---> ...
                                   \ /
                        ... --->--( 4 )---> ...
                                   /
                        ... --->--'

                Figure 3: The concept of a mouth state.

At each of the mouth state entry, there may be different incoming recipe.  An
example is shown in figure 4. The operation 'op(i)' for each state is 'x=x+1'.

                                              x=x+1
                       .-------------->---------------. [x=x(0)+1]
                      /                                \
                   ( 0 ) [x=x(0)]                     ( 3 )---> ...
                      \                                /
                       '--->( 1 )----->( 2 )----->----' [x=x(0)+3]
                       x=x+1      x=x+1       x=x+1

                   Figure 4: Recipes meet in mouth state 3.

At the entry to state 3, there are two recipes for 'x'. First, there is recipe
'R(0)' which is concatenated with 'op(3)'. It becomes "x=(0)+1". Second, there
is recipe 'R(2)' concatenated with 'op(3)' which becomes "x=x(0)+3".  Both are
different, so there is only one way to determine 'x': it must be computed  upon
entry into the state.  A recipe for state 3 which can be a basis for subsequent
linear states must rely on the stored value for it.

               x(3)=x(0)+1 
           ... ------. 
                      \     [x=x(3)]      x=x+1       [x=x(3) + 1]
                     ( 3 )---------------------->( 4 )------- ...
                      /
           ... ------' 
               x(3)=x(0)+3 

                   Figure 4: Recipes in a mouth state.

Note, that the register 'x(3)' is not part of the SOV. Thus, the newly entered
computations 'x(3)=x(0)+1' and 'x(3)=x(0)+3' are not operations 'op(i)' as
defined earlier and are not subject to further considerations.  Now, let the
process of 'interference' be defined as follows.

DEFINITION: Interference

    The process of 'interference' develops a recipe 'R(i)' for a mouth state.
    First, it concatenates the recipe of each incoming state with its operation
    'op(i)'. The result is the set of entry recipes. Second, the set of entry
    recipes is used as a basis to determine 'R(i)'. Along with the recipe
    new non-SOV operations may be injected into the state machine. Those
    operations store reference values which are required by 'R(i)'.

Interference cannot happen, if the set of entry recipes is incomplete. That is,
if for one entry the recipe cannot be determined, then the interference of 
the mouth state cannot be accomplished.

Commonalities between recipes are translated into changed constants. When
differences are detected, they require values to be stored in registers for
later reference. Once, a mouth state has a determined recipe, it can act
as a spring for the walk along linear states.

-------------------------------------------------------------------------------

THE WALK ALONG LINEAR STATES

The recipes for states are determined by a walk along linear states. While
linear states have only one entry, they may have transitions to more than one
state. So, the walk along linear states is a recursive 'tree-walk'. The
termination criteria for the walk along linear states is defined as follows.

DEFINITION: Termination criteria for walk along sequence of linear states.

    A recursive walk along sequences of linear states does not enter the
    state ahead, if 

       (i)   there is no state. The current state is a terminal.
       (ii)  the state ahead is a mouth state.
       (iii) the state ahead complies to the conditions of a spring.

The first condition comes natural. The second condition exists, because recipes
cannot be accumulated beyond mouth states. As a direct consequence, the walk
can never go along loops, since a loop requires a state with more than one
entry. A mouth state, however, is never part of the walk according to condition
(ii). The third condition tells that the walk stops where another walk begin or
began.  With these concepts, a first draft of an algorithm for the
determination of recipes can be defined.

          (*) Start.
          (*) begin_list = springs extracted from state machine.
   .----->(*) perform linear walks starting from each spring.
   |          --> determine R(i) along linear states until terminal,
   |              mouth, or springs.
   |          --> entries of mouth states receive entry recipes.
   |      (*) interference in mouth states with complete sets of entry
   |          recipes.
   |          begin_list = determined mouth states
   '- no -(*) begin_list empty?
          (*) Stop.

        Algorithm 1: Determination of recipies.

When this algorithm comes to an end, there might be still mouth states with
undetermined entries. The only possible reason for that are mutual dependencies
between mouth states. Such dead-locks are handled in the next section.

PROOF: 
    
     (1) The begin_list in algorithm 1 is <=> there are no new springs.

         That is, either there were no mouth states, or the mouth states that 
         exist were not resolved. 

     (2) A mouth state is only unresolved, if there is at least one entry which
         cannot be determined. An entry into a mouth state which is
         undetermined must originate from an unresolved mouth state.

         With (1) it follows:
        
         For every unresolved mouth state 'i' there is at least one state 'k'
         on which it depends which is also unresolved.

     (3) If a state 'a' depends on 'b' and 'b' depends on 'c', then 'a' also
         depends on 'c'. For an unresolved state a dependency sequence can
         be specified of the form

                           a <-- b <-- c <-- ...

         briefly, let the set of states on which 'a' depends be 

                           D(a) = a <-- (b, c, ...)
         
     (4) A state machine has a finite number of states. 

     (5) from (3) and (4): The set of states on which an unresolved mouth state
         'a' depends is finite.

     (6) Let 'p' be the last state added to 'D(a)'.
    
         from (2) and (3): for a state 'p' to belong to D(a), it must rely on 
         an unresolved state 'q'.

     (7) from (6) and the restriction of (5): 'q' must be element of D(a).

     (8) if 'q' belongs to 'D(a)' before, than it must depend on 'p'.

     => There is at least one 'p' depending on 'q' and 'q' depending on 'p'
        in the set of 'D(a)'.
         
However, not every unresolved state is locked into a mutual dependency.

                             .---->---.             
                          ( 0 )      ( 1 )------>( 2 ) 
                             '----<---'            
                     
              Figure 6: Unresolved state 2, not having a mutual dependency.

-------------------------------------------------------------------------------

DEAD-LOCK STATES

Dead-lock states are states with undetermined entries. Their entries are 
undetermined, because they depend on states, which in turn depend on them.
An example is shown in Figure 4.

                           .------------>( 2 )
                     A     |             /   \
                ... ---->( 1 )          (     )
                           |             \   /
                           '------------>( 3 )
         
        Figure 4: A dead-lock of mouth states 2 and 3.

In the example shown in figure 4, both states 2 and 3 only experience the
effects of operation 'A'. For an algorithm, a formal procedure is required
to determine the entries of dead-lock states. 

DEFINITION: Dead-lock state.

    A dead-lock state is a mouth state 'i' which could not be resolved with 
    algorithm 1. As a direct consequence, it

       (i)   has at least one entry with no associated 'R(p(i))'.
      
       (ii)  has entries originating from other dead-lock states.

The first characteristic is a tautology to the fact that algorithm 1 was not
able to resolve it. The second characteristic is a logic conclusion from the
fact algorithm 1 stops only when it cannot use a dependency to resolve another.
Thus, there must be some mutual dependency, such as 'A' depends on 'B', depends
on 'C', which depends on 'A'. 

Dependencies correspond to paths of linear states between mouth states. If
there are mutual dependencies, then, this corresponds to loops in the graph
model.

DEFINITION: Dead-Lock Group.

    A set of mouth states where each state from the set depends on all other
    states, is called a dead-lock group. As a direct consequence of mutual
    dependencies, each state in a dead-lock group is connected to at least one
    loop.

A dead-lock group cannot be divided into two sub-groups. If any two states 'i'
and 'k' belong to a group of dead-locks states, then they depend on each other
mutually. If either one belonged to a group without the other, then this group
cannot be a dead-lock group. It would be missing a mutual dependency. 

However, there may be more than one dead-lock group where one even depends
on the other. Consider a dead-lock group where states 'i' and 'k' are mutually
dependent. State 'k' depends on a state 'p', but 'p' not on 'k'. However, 
'p' is mutually dependent on 'q'. This is depicted in figure 6.

                     .---->---.             .---->---.
                  ( i )      ( k )<------( p )      ( q )
                     '----<---'             '----<---'

                  Figure 6: Dependent dead-lock groups.

The 'p' an 'q' build a dead-lock group, and so does 'i' and 'k'. All four 
states do not build a dead lock group. 'i' and 'k' depend on 'p' and 'q'.
however, 'p' and 'q' do not depend neither on 'i' nor on 'k'.

In the case that the entry depends on the output of a dead-lock state of
another group, then that other group must be determined first.  

A circular
dependency, such as "group A depends on group B, depends on group C, which
depends on group A", is impossible, because this would make all states of A, B,
and C mutually dependent. Therefore, the states of those groups were,
actually, a dead-lock group on their own. 

STATEMENT:

    Groups of dead-lock states can be organized hierarchically.  Groups on
    which others depend can be determined before groups which depend on them.
    
    As a direct consequence, for any set of groups of dead-lock states there
    is a sequence of resolution so that all groups become determined.

From the existence of a non-cyclic hierarchy of dependence between dead-lock
state groups, it can be concluded that there is always at least one dead-lock
group with no dependency to another. Once this dead-lock group is resolved, 
another group becomes independent, and can be resolved. Thus, it is safe to
assume that by iteratative resolution of independent groups, finally all 
dead-lock states end up being determined.

                          dead-lock group
                         .----------------------.
                 Accu(1) :      .---->----.     : Accu(4)
            .-------------->( 2 )        ( 4 )<-------
            |            :   / \'----<----'     :
      --->( 1 )          :  (   )               :
            |  Accu(3,1) :   \ /                : Accu(3,5)
            '-------------->( 3 )<----------------------------( 5 )<--- 
                         :                      :
                         '----------------------' 

         Figure 5: Dead lock states and their entries.

Figure 5 shows a dead-lock group where all entries into it are determined. The
only influence from outside this group comes through 'Accu(2)', 'Accu(3,1)',
'Accu(3,5)' and 'Accu(4)'. Since states are mutually dependent, there
necessarily exist loops inside a dead-lock group. Thus, the number of
transitions inside the group can only be determined at run-time. The process
of specification of an inherent recipe action inside a dead-lock group,
can be defined similar to interference as follows.

DEFINITION: R(group) -- Inherent Recipe

   The 'inherent recipe' R(group) is the recipe that appears at any entry into
   a dead-lock state from another dead-lock state. 

   R(group) is determined from the set of specified accumulated actions, at
   specific entries of states of the group. 

   R(group) can either not rely on transition numbers at all, or they must
   be relative to the first state through which the group is entered.

   R(group) is specified at each entry of the group, except for the specific
   entries which are previously determined.

An issue remains: What if on the linear paths between the dead-lock mouth
states there is a state with an operation? Clearly, this state cannot be a
spring, otherwise, the mouth state's entry on the other end would be determined
which it is not. Operations of linear states which are not springs accumulate.
Further, dead-lock groups incorporate loops. So, The position where the
operation occurs in the sequence and in what sequence with other operations
cannot be determined.



-------------------------------------------------------------------------------

All .txt files in this directory that describe action reductions are following
this scheme. The 'doubt' discussion shall demonstrate the deepness of thought
that has been put into the development. All doubts, of course, should be
debunked.

-------------------------------------------------------------------------------

