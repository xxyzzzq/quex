Operation Reduction/Operation Postponing

(C) Frank-Rene Schaefer
-------------------------------------------------------------------------------
ABSTRACT:

This file describes the theoretical background for the process applied by Quex
used to reduce the number of operations or to postpone operations. Any write
operation that can be avoided during state transitions may bring a strong
performance increase (due to avoided cache misses, for example). Operations are
preferred to be postponed, because earlier states are passed more often than
later states.

-------------------------------------------------------------------------------
SITUATION:

Incoming characters cause state transitions. Transitions are adorned with
operations, such as 'store last acceptance'. At some point, an incoming
character does not fit a transition map of the current state and the state
machine exits.  Upon such a 'drop-out', some consequences are derived  based on
the passed operations and the current state. The steps in the run through a
state machine are depicted in figure 1.


                         .----------<---------------.
                         |                          |
               Begin -------> Operations -----> Transitions -----> Drop-Out
                                                       

                   Figure 1: The run through a state machine.

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
*back-propagation* of needs. A state or a terminal which requires a specific
variable tags all of its predecessor states with this requirement. That is, if
a state 'k' requires a variable 'x' than 'x is element of SOV(i)' for all 'i'
in the set of states that lead to 'k'.

A state machine changes variables of the SOV. These changes are consequences of
operations that happen upon entry into states. Let an 'operation' be defined as
follows.

DEFINITION: op(i) -- Operation 

    The modification on the SOV upon entry into a state 'i' is called an
    operation 'op(i)'. With 'x' as the setting of the SOV before entry
    into a state 'i', the setting of the SOV in state 'i' becomes

                         SOV(i) = op(i)(x)

That is, 'op(i)' is a function or a procedure that is applied on the set of
variables of concern. All investigated behavior along the state machine 
concentrates on operations on the SOV.

-------------------------------------------------------------------------------

LINEAR STATES AND MOUTH STATES:

Two central concept of the analysis algorithms are 'linear states' and 'mouth
states' as they are defined in the paragraphs to follow. 

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
along a sequence of linear states, then SOV(i) can be determined by SOV(k)
through

                 SOV(i) = OP(i,k)(SOV(k))

That is, if SOV(k) is determined, then SOV(i) can be determined without the
operations along the path from 'k' to 'i'.  Figure 2 displays an example, that
shows how this can be used to reduce computational effort. 

                     x=x+1       x=x+1       x=x+1        
           ... ( a )------>( b )------>( c )------>( d )------> ...


             Figure 2: A string of linear states

For an exit in state 'd' the operations can be described in general terms as

                   SOV(b) = op(b)(SOV(a))
                   SOV(c) = op(c)(SOV(b))
                   SOV(d) = op(d)(SOV(c))
                          = op(d)(op(c)(SOV(b)))
                          = op(d)(op(c)(op(b)(SOV(a))))
                          = OP(e,a)(SOV(a))
                 
The SOV in figure 2 is 'x'. The operation 'op(i)' for all states in figure 2 is
'x = x + 1'. Thus, with 'x(i)' as the 'x' in state 'i' the sequence in the
becomes:
    
                          x(b) = x(a) + 1
                          x(c) = x(b) + 1
                          x(d) = x(c) + 1
                         
The 'x(d)' in state 'd' can be determined in one operation:
                         
                          x(d) = x(a) + 3
       
The formula for 'x(d)' together with 'x(a)' build the recipe to determine the
SOV in state 'd' without knowing the previous operations along the path.  In
the example above, a longer sequence of additions was transformed into a single
addition.  Let the term recipe be define for the context of this discussion.

DEFINITION: R(i) -- Recipe 

   A recipe 'R(i)' for a state 'i' is a description of how to determine 
   the SOV(i) when the state has been entered. It maps

                     (s, r, c) ---> SOV(i)

   where 's' is the current state including his variables. 'r' is a setting of
   registers that store temporary data, and 'c' is a set of constants. 

Along a sequence of linear states, there is an obvious relation between a
recipe and the concatinated operations

                   SOV(i) = OP(i,k)(SOV(k))

If 'i' is reached from 'k' by a sequence of linear states, then the 'SOV(k)' and
the OP(i,x) build together the recipe R(i). 'SOV(k)' is an example of content
stored in registers, i.e. the 'r' in the definition of a recipe. An example for
constants 'c' can be observed in the example from figure 2, where 'x' was
computed as the content of 'x' stored in state 'a' plus a constant number. 

An example for a state variable in a recipe would be, for example, the
computation of the lexeme length 'length(i)' based on the distance to the
position of first character 'ip0'. Let 'ip' be the pointer to the position where
the current character is located. Then the lexeme length can be expressed as

                        length(i) = (ip - ip0)

and 'ip' is a state variable, i.e. an element of 's' from the definition of a
recipe. The iterative development of recipes can only start at a state where
the recipe to compute the SOV is determined. Only then, any previous history
can be dropped from consideration, because it is reflected in the state's
recipe.

DEFINITION: Spring

    A spring is a state where a walk along linear states can begin. For a state
    'i' to act as a spring, the recipe 'R(i)' must be determined.

If the spring is guides to a linear state, then this linear state can
determine its recipe through concatenation, as discussed earlier. Let this
process of iterative concatenation be called accumulation.

DEFINITION: Accumulation

    The process of determining a recipe of a linear state base on the recipe
    of a predecessor state is called 'accumulation'.

If a linear state that received a recipe through accumulation, then it can now
itself act as a basis for accumulation for successor linear states. This
process can be repeated until a mouth state is reached.  Mouth states are the
counterpart to linear states. 

DEFINITION: Mouth State

    A mouth state is a state that is entered from more than one state. An 
    example is depicted in figure 1.

                        ... --->--.   .---> ...
                                   \ /
                        ... --->--( 4 )---> ...
                                   /
                        ... --->--'

                Figure 3: The concept of a mouth state.

At each entry of the mouth state, there may be a different incoming recipe.  An
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
'R(0)' which is concatenated with 'op(3)'. It becomes "x=x(0)+1". Second, there
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

DEFINITION: Termination criteria for walk along linear states.

    A recursive walk along linear states does not enter the
    state ahead, if 

       (i)   there is no state. The current state is a terminal.
       (ii)  the state ahead is a mouth state.
       (iii) the state ahead complies to the conditions of a spring.

The first condition comes natural. The second condition exists, because recipes
cannot be accumulated beyond mouth states. As a direct consequence, the walk
can never go along loops, since a loop requires a state with more than one
entry. A mouth state, however, is never part of the walk according to condition
(ii). The third condition tells that the walk stops where another walk begins or
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
undetermined entries. The only possible reason for that are circular dependencies
between mouth states. 

PROOF: 
    
begin_list in algorithm 1 empty <=> there are no new springs.

=> Either: (i) All mouth states were resolved (-> would be springs), or 
           (ii) There are unresolved mouth states, because not all entries
                of those states could be determined.                        (1)

From case (i) no statement about unresolved mouth states can be derived. Case
(ii) makes the first usable statement. Let

        U := set of unresolved mouth states after algorithm 1 ended.        (2)

An entry into a mouth state which is undetermined must be connected through a
linear state sequence, or directly, with a mouth state which is undetermined.
Let the fact that a state 'p' has an undetermined entry originating from 'q' be
called a dependency of 'p' on 'q' and let it be written as 

                               p <-- q

'q' must be undetermined, so it follows

                      p <-- q and p in U => q in U                          (3)

If 'q' depends on 'u', then logically 'u' influences 'q' and 'p'. Thus, 

               p <-- q  and q <-- u   <=>   p <-- { q, u }                  (4)


Let the set of dependencies for a state 'p' be defined as 

                          D(p) = { q, u, ...}                               (5)

which includes every state on which 'p' depends with its 'unresolvedness'. The
number of states in a state machine is finite, thus the size of U is finite. 
It follows 

                         size of D(p) = finite                              (6)
         
From (3) follows that any state 'i in D(p)' must be unresolved, thus it must
be dependent on an unresolved state 'k'. From (4), it follows that if 'p'
depends on 'i', then it also depends on 'k', i.e. 'k in 'D(p)'. 

               i in D(a) and i <-- k => k in D(a)

If the states of 'D(a)' were displayed as dots in a plane, and the dependencies
between elements of 'D(a)' as arrows, then there would be 'n+1' arrows on 'n'
dots. This is only possible, if there is at least one loop. A loop is a circular
dependency.

    size of U is not empty <=> there is at least one circular dependency    (7)

what was to be proven.  However, not every unresolved state is locked into a
circular dependency. An example is shown in figure 6. There, state 2 is
unresolved because it depends on state 1. However, state 2 is not circularly
dependent on state 1. State 1, on the other hand, is unresolved, because it
is mutually depends on state 0.

                             .---->---.             
                          ( 0 )      ( 1 )------>( 2 ) 
                             '----<---'            
                     
     Figure 6: Unresolved state 2 depends on unresolved state 1, but is 
               itself not part of a circular dependency.

-------------------------------------------------------------------------------

DEAD-LOCK STATES

Dead-lock states are states with undetermined entries and circular
dependencies.  An example is shown in Figure 4.

                           .------------>( 2 )
                   op(1)   |             /   \
                ... ---->( 1 )          (     )
                           |             \   /
                           '------------>( 3 )
         
        Figure 4: A dead-lock of mouth states 2 and 3.

In the example shown in figure 4, both states 2 and 3 only experience the
effects of operation 'op(i)'. 

DEFINITION: Dead-lock state.

    A dead-lock state is a mouth state 'i' which could not be resolved with 
    algorithm 1. Additionally, it is part of a circular dependency with at least
    one other unresolved mouth state. As a direct consequence, it follows

       (i)   There is at least one entry to state 'i' with no associated 
             recipe 'R(p(i))'.
      
       (ii)  'i in D(i)', state 'i' is element of the set of states on which
             it depends.

The first characteristic is a tautology to the fact that algorithm 1 was not
able to resolve it. The second characteristic is a reformulation of the finding
of the PROOF of the last section.  Dependencies correspond to paths of linear
states between mouth states. If there are circular dependencies, then, this
corresponds to loops in the graph model.

DEFINITION: Dead-Lock Group.

    A set of mouth states where each state from the set depends on all other
    states, is called a dead-lock group. As a direct consequence of circular
    dependencies, each state in a dead-lock group is connected to at least one
    loop.

A dead-lock group cannot be divided into two sub-groups. If any two states 'i'
and 'k' belong to a group of dead-locks states, then they depend on each other
circularly. If either one belonged to a group without the other, then this group
cannot be a dead-lock group. It would be missing a circular dependency. 

However, there may be more than one dead-lock group where one group depends on
the other. Consider a dead-lock group where states 'i' and 'k' are circularly
dependent. State 'k' depends on a state 'p', but 'p' not on 'k'. However, 'p'
is circularly dependent on 'q'. This is depicted in figure 6.

                     .---->---.             .---->---.
                  ( i )      ( k )<------( p )      ( q )
                     '----<---'             '----<---'

                  Figure 6: Dependent dead-lock groups.

The 'p' an 'q' build a dead-lock group, and so does 'i' and 'k'. All four
states do not build a dead lock group. 'i' and 'k' depend on 'p' and 'q'.
However, 'p' and 'q' do not depend neither on 'i' nor on 'k'.  In the case that
the entry depends on the output of a dead-lock state of another group, then
that other group must be determined first.  

A circular dependency, such as "group A depends on group B, depends on group C,
which depends on group A", is impossible, because this would make all states
of A, B, and C circularly dependent. Therefore, the states of those groups
were, actually, a dead-lock group on their own. Since dead-lock groups are
not divisible, 'A', 'B', and 'C' cannot exist as independent groups.

STATEMENT:

    Groups of dead-lock states can be organized hierarchically.  Groups on
    which others depend can be determined before groups which depend on them.
    
    As a direct consequence, for any set of groups of dead-lock states there
    is a sequence of resolution so that all groups become determined.

From the existence of a non-cyclic hierarchy of dependencies between dead-lock
state groups, it can be concluded that there is always at least one dead-lock
group with no dependency to another. Once this dead-lock group is resolved,
another group becomes resolvable. Thus, by iterative resolution of
independent groups, finally all dead-lock states end up being determined.

                          dead-lock group
                         .----------------------.
                R(1)op(2)|      .---->----.     | R(6)op(4)
            .-------------->( 2 )        ( 4 )<---------------( 6 )<---- 
            |            |   / \'----<----'     |
      --->( 1 )          |  (   )               |
            |   R(1)op(3)|   \ /                | R(5)op(3)
            '-------------->( 3 )<----------------------------( 5 )<--- 
                         |                      |
                         '----------------------' 

         Figure 5: Dead lock states and their entries.

Figure 5 shows a dead-lock group where all entries into it are determined. The
only influence from outside this group comes through 'R(1)', 'R(5)', and
'R(6)'.  Due to the loops in the graph, one cannot preview for any of the
states '2', '3', or '4' in what order or combination the recipes are applied.
Further, no assumptions can be made about the number of transitions which are
made from the entry into the group until a specific state is reached. These
constraints are stronger than the constraints for interference at mouth states.

DEFINITION: Dead-Lock Group Interference

    The process of 'dead-lock group interference' develops a recipe 'R(i)' for
    all unresolved mouth states that are part of a dead-lock group. 
   
    All determined entries are collected into the 'mega-set' of entry recipes.
    Those values of the SOV which are not uniform must be stored in register.
    The resulting recipe 'R(group)' rely on those stored values.
   

An issue remains: What if on the linear paths between the dead-lock mouth
states there is a state with an operation? Clearly, this state cannot be a
spring, otherwise, the mouth state's entry on the other end would be determined
which it is not. Operations of linear states which are not springs accumulate.
Further, dead-lock groups incorporate loops. So, The position where the
operation occurs in the sequence and in what sequence with other operations
cannot be determined. There is only one way to deal with that: The resulting
recipe must be included into the dead-lock state interference. In the state
itself, non-uniform values of the SOV must be stored in registers.

-------------------------------------------------------------------------------

