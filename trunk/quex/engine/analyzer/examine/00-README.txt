Operation Reduction/Operation Postponing

(C) Frank-Rene Schaefer
-------------------------------------------------------------------------------

ABSTRACT:

This file describes the theoretical background for the process applied by Quex
used to reduce the number of operations or to postpone operations.  The
optimization uses the fact that intermediate values which are developed during
the state transitions are not visible to the outer observer. Instead, only the
values are important that are present upon exit from the state machine.

Figure 1 shows a very simple state machine consisting of four states.  The
dotted lines indicate 'drop-out', i.e. a path that is taken to exit the state
machine.  In the original state machine, as shown in figure 1.a, the content of
'x' is increment upon each transition. When the state machine is left in state
3, for example, three such increments must have taken place. In figure 1.b an
optimized representation of the state machine is shown.  There, value of 'x' is
only determined upon exit.  No increments happen during transitions. Only upon
exit 'x' is assigned the predetermined value. The balance on computational
effort is obvious.

     
         a)          x=x+1        x=x+1        x=x+1
              ( 0 )------->( 1 )------->( 2 )------->( 3 )
                : exit       : exit       : exit       : exit
                :            :            :            :
    
         b)
              ( 0 )------->( 1 )------->( 2 )------->( 3 )
                : exit       : exit       : exit       : exit
                :            :            :            :
               x=0          x=1          x=2          x=3
    
             Figure 1: Original and optimized state machine.
                 

The analysis requires a state machine which is composed of 'single-entry
states'. That is, upon entry into a state the same operations are executed
independently from which the state is entered or through which transition.  A
single-entry state is shown in figure 2.a. The optimization transforms the
single-entry state machine into a 'multi-entry state machine'.  That is, the
operations applied upon entry into a state may be different dependent from
which state or through which transition the entry happens.  A multi-entry state
in shown in figure 2.b.

           a)
     
                  ---------.
                            \                       .-----.
                  -----------+---[ operations ]----( state )----->   
                            /                       '-----'
                  ---------'       
     
           b)
     
                  ---[ operations 0 ]----.
                                          \         .-----.
                  ---[ operations 1 ]------+-------( state )----->  
                                          /         '-----'
                  ---[ operations 2 ]----'       


      Figure 2: Two approaches of state modelling: a) Single entry state. 
                b) Multi-entry state. 
                
The analysis tries to exploit predictable sequence of operations along state
transitions. This is done by compensating them through a single operation or by
postponing them to a state as late as possible.  Operations are preferably
postponed, because earlier states are passed more often than later states.


-------------------------------------------------------------------------------

BASICS:

Along the transitions of a state machine many different operations may occur
which do not necessarily share the same subject. Some operations determine the
last accepted pattern, the input position to be restored upon acceptance, the
line and column numbers, the checksum value of a lexeme, or the sum of grapheme
widths of the lexeme's characters, and so on. The term 'investigated behavior'
is defined to specify a focus of analysis.

Let the sets of variables which are associated with an investigated behavior be
called DCV.

DEFINITION: DCV -- Description of Concerned Variables

    The 'DCV' of an investigated behavior describes the set of variables which
    are of concern. 

A 'DCV' may be a simple list of variable names or a abstract description such
as 'all variables related to input position storage' where the number of
variables is open.  As a consequence of transitions, a state machine changes
the content of variables. However, not all variables of an DCV are necessarily
relevant for all states. Let the set of required variables be defined as

DEFINITION: RV(i) -- Set of Required Variables

    'RV(i)' defines the variables which are required in state 'i'. The
    variables must be sufficient

      (i)  to implement the investigated behavior upon drop-out and
      (ii) to develop the DCV settings of all successor states.

In constrast to 'DCV', the set of variables in 'RV(i)' must be concrete.
Instead of the loose statement 'all variables related to input position
storage', the specific variables must be specified. 

'RV(i)' can be determined by *back-propagation* of needs. A state which
requires a specific variable tags all of its predecessor states with this
requirement. That is, if a state 'k' requires a variable 'x', then 'x is
element of 'RV(i)' for every state 'i' that lies on the path to 'k'.

Assume for example, that the lexeme length is not required in a terminal. Then
any operation contributing to the computation of the lexeme length is
redundant.  No state on a path to this terminal is required to perform lexeme
length related operations, except that another successor state requires it.
Let setting of required variables be defined as follows.

DEFINITION: V(i) -- Setting of RV(i)

    The term 'V(i)' represents the settings of all required variables 'RV(i)'
    after a state 'i' is entered and before it transits further. 
    
An elementary unit that modifies the content of a variable is called an
'operation', as defined here:

DEFINITION: op(i) -- Operation 

    A modification to a one or more variable of 'RV(i)' upon entry into a state
    'i' is called an operation 'op(i)'. 
    
With 'V(h)' as the setting before entry into a state 'i' and 'V(i)' as the
setting in state 'i' the operation 'op(i)' describes the modification by 

                         V(i) = op(i)(V(h))

With the aforementioned definitions, the investigated behavior can be defined
precisely.

DEFINITION: Investigated Behavior 

   The 'investigated behavior' determines the scope of analysis. It is
   specified by a description of concerned variables 'DCV', the required
   variables 'RV(i)' for each state 'i', the related operations 'op(i)' and
   their *nominal behavior*.
    
A 'nominal behavior' defines what needs to happen during the state machine
transitions.  For example, the nominal behavior for line number counting is
that the line number variable should be increased upon newline and remain the
same upon the occurrence of any other character. 

-------------------------------------------------------------------------------

LINEAR STATES AND MOUTH STATES:

Two central concepts are required for the further discussion: 'linear states' and 'mouth
states'.  They are defined in the paragraphs to follow. 

DEFINITION: Linear State

    A linear state is a state that is entered only from one predecessor state.

The concept of a linear state is shown in figure 3. The operation 'op(i)' works
on the 'V(k)' before entry and produces 'V(i)'. Note, that a linear state
may have transitions to multiple successor states, but only on predecessor state.


                                                      .---> 
                                                     /
                                                   .-.
                      --------[ op(i) ]---------->( i )---> 
                     V(k)              V(i)    '-'

                    Figure 3: The concept of a linear state.


DEFINITION: Mouth State

    A mouth state is a state that is entered from more than one predecessor 
    state. 
    
Figure 4 displays the concept of a mouth state and the development of the
'V(i)' based on the DCVs of predecessor states.

                  ------>--.  
                 V(a)       \ 
                             \                       .-.
                  ------>-----+---[ op(i) ]---------( i )---> 
                 V(b)        /                 V(i)  '-'
                            /
                 ...       :
                  ------>--'
                 V(z)

                    Figure 4: The concept of a mouth state.

In a linear state the 'V(i)' can be determined based on the predecessor's
DCV and the 'op(i)'

            V(i) = op(i)(V(k))                                          (1)

with 'k' as the one and only predecessor state. If 'V(k)' is known, then
'V(i)' of a linear state is known off-line purely from the consideration of
the state machine.  In a mouth state 'V(i)' is be determined depending on the
state from where the transition originates.

                    /  op(i)(V(a))  if entry from state 'a'
                    |  op(i)(V(b))  if entry from state 'b'             (2)
            V(i) =  |   ...
                    |  
                    \  op(i)(V(z))  if entry from state 'z'

Let 'recipe' be the procedure to determine the DCV in a state without
considering any previous operation. That is, if for all states all recipes are
known, then all operations along the state machine transitions can be removed.
Let the term recipe be defined as follows.

DEFINITION: R(i,k), R(i) -- Recipe 

   Let 'R(i,k)' indicates the 'recipe' to determine 'V(i)' upon entry into a
   state 'i' from a predecessor state 'k'.  It is derived from the operation
   'op(i)' and 'R(k)'.  The recipe's procedure uses solely the following
   inputs:

          * 'h(i)', the hidden variables of state machine.
          * 'A', the setting of auxiliary variables.

   It implements the mapping

                  (h(i), A) ---> V(i)                                   (3)

   Let 'R(i)' indicate the recipe which appears to the successor states of
   state 'i'.

Hidden variables are all variables of the state machine other than the 'state'.
A lexical analyzer state machine has, for example the lexeme start position,
  the buffer limits, the stream position, etc. as hidden variable.  

The fundamental difference between 'R(i)' and 'V(i)' is that the former is a 
procedure and the latter represents the values which are produced.

The simplest form of a recipe is the setting with constant values.  For
example, at a state entered by the newline character the recipe for 'column
number' may be 'column number = 0', because a new line begins. The advantage of
recipes is demonstrated figure 5.


    a)        
            'accept=10'        'accept=12'        
       ... ------------>( 1 )-------------->( 2 )----> ...
                          :                   :
                    goto T(accept)      goto T(accept)

    b) 
       ... ------------>( 1 )-------------->( 2 )----> ...
                          : 'accept=10'       : 'accept=12'              
                          :                   :
                      goto T10            goto T12

     Figure 5: Equivalent state sequences. a) Relying on operations along
               transitions. b) DCVs determined by recipes.

In figure 5.a operations are executed at each transition step. They assign
identifiers to the last acceptance variable 'accept'. This assignment happens
even if states '1' and '2' are passed by and later states may detect another
acceptance. Upon drop-out from state 1 or 2 a conditional goto to a terminal is
applied based on the setting of 'accept'. 

In figure 5.b the operations along transitions are completely removed. The
recipes determined the acceptance a priori, so that a direct goto to the
correspondent terminal can be applied.  Clearly, the second approach requires
no computational effort during transitions and lesser effort upon drop-out.

With the concepts of this section, the overall goal can be formulated. The
analysis transforms the given single-entry state machine based on operations
into a multi-entry state machine based on recipes. Observing only the entry and
exit, the changes to the DCV must comply to the nominal behavior. 

-------------------------------------------------------------------------------

BASICS ON PROPAGATION OF RECIPES

A recipe for one state is the basis for the development of the recipe of its
successor state. For a linear state, equation (1) described how 'V(i)' is
determined from the predecessor's 'V(k)' and the entry operation 'op(i)'. If
'V(k)' can be determined by a recipe 'R(k)', then 'V(i)' becomes

                     V(i) = op(i)(R(k))                                     (4)

Since, a recipe 'R(k)' is already independent of operations along transitions,
the recipe for 'V(i)' becomes nothing else than the expression that
determines it. That is,

                     R(i) = { op(i)(R(k)) }                                 (5)
                 
The above definition tells that recipes can only come from recipes. An
important step towards the answer where the first recipe comes from is the
concept of a 'historyless recipe'. It is based on the concept of 
'historyless variables'.

DEFINITION: HLV(i) -- Historyless Variables

   The set of historyless variables in a state 'i' is given by 
 
                        HLV(i) \subset RV(i)                                (6)

   For all 'v in HLV(i)' determined by 'v from op(i)' it holds that 

                   v not a function of V(k) forall 'k' in P(i)              (7)

   where 'P(i)' is the set of predecessor states of 'i'.

A variable can only be history less, if 'op(i)' assigns a constant to it which
is independent of previous states or paths.  When history becomes important,
then the development of a variable setting must be accomplished at
'run-time' using system memory. This is accomplished by 'auxiliary
variables'.

DEFINITION: A, A(v) -- Auxiliary Variables

   The term auxiliary variable 'A(v)' specifies a variable that may store the
   content of the variable 'v' at run-time. 'A' names the set of all auxiliary
   variables.

DEFINITION: HLR(i) -- Historyless Recipe

   For a given state 'i' the 'HLR(i)' expresses the effect of 'op(i)' on the
   set of required variables 'RV(i)' in isolation of previous history.  That
   is, for each variable 'v in RV(i)' it holds

                    /   v from op(i)    for v in HLV(i)                
                v = |                                                       (8)
                    \   A(v)            else.

The historyless recipe is only correct, if 'A(v) = v' has been stored upon
entry into state 'i' after 'op(i)' has been applied for all 'v not in HLV(i)'.
A historyless recipe can be considered as start for analysis if the set of
required variables is equal to the set of historyless variables. Accordingly, a
spring can be defined.

DEFINITION: Spring

    A state 'i' where all required variables 'RV(i)' can be determined by 
    the historyless recipe 'HLR(i)' is called a spring. It holds

                          RV(i) = HLV(i)

    The recipe 'R(i)' for a spring state is determined by
    
                          R(i) := HLR(i)

In other words, for a spring there is no 'v' determined by 'A(v)' as shown in
equation 8.  In equation 5 it is demonstrated how a recipe 'R(i)' is derived
from a predecessor's recipe 'R(k)' and a state 'i'-s operation 'op(i)'. This
procedure is defined here as 'accumulation'.

DEFINITION: Accumulation

    Given a state 'i', its predecessor state 'k', the entry operation 'op(i)'
    the predecessor's recipe 'R(k)', the recipe to 'R(i,k)' is equivalent
    to the concatenated operations of 'op(i)' and 'R(k)'.

    A prerequisite for accumulation is that 'R(k)' of the predecessor is 
    determined.

EXAMPLE:
                  op(b)=        op(c) =      op(d) =
                    x=x+1         x=x+1         x=x+1        
            ( a )-------->( b )-------->( c )-------->( d )--------> ...


                  Figure 6: A sequence of linear states.


Figure 6 displays an example of an DCV containing a single variable 'x'. The
operations 'op(i)' upon transition are 'x=x+1' for all states. That is 'x' is
incremented by 1 at each step. Let the 'A(x,a)' signify 'A(x)' as it was
assigned upon entry into state 'a'. The recipe in state 'a' solely restores
what has been stored.

               R(a) = { x := A(x,a) }                                     (6)

The recipe 'R(b,a)' must be equivalent to the concatenated execution of 'op(b)'
and 'R(a)', i.e.

                   { x := A(x,a) }
                   { x := x + 1 }
So, 
               R(b) = { x := A(x,a) + 1 }                                 (7)

This rule applied repeatedly for the states 'c' and 'd' leads to

               R(c) = { x := A(x,a) + 2 }
               R(d) = { x := A(x,a) + 3 }                                 (8)

If the state machine exits at 'a', 'b', 'c' or 'd' the content of 'x' can be
determined without relying on the intermediate operations { x:=x+1 }. This
is shown in figure 7.
 
          ( a )-------->( b )-------->( c )-------->( d )--------> ...
                          :             :             :
                        x=A(x,a)+1    x=A(x,a)+2    x=A(x,a)+3


          Figure 7: Recipes upon exit replace transition operations.

The repeated accumulation of recipes along linear states comes to an end at
mouth states.  Equation (2) described the development of the DCV in mouth
state. Using the concept of a recipe, the equation can be rewritten as

                     /  R(i,p)  if entry from state 'p'
                     |  R(i,q)  if entry from state 'q'
            V(i) = |   ...                                                (9)
                     |  
                     \  R(i,z)  if entry from state 'z'

The applied recipe depends on the origin state of the transition which is only
determined at run-time. However, a recipe 'R(i)' for a mouth state can be
determined as follows. For each variable of the DCV there are two
possibilities:

   Homogeneity:   All entry recipes apply the exact same process to
                  determine the variable's content.

   Inhomogeneity: Two or more entry recipes apply a different process
                  to determine the variable's content.

If a variable 'v' is determined homogeneously, then the part of the recipes
that determines it can be overtaken into 'R(i)'. Otherwise, the value must be
computed upon entry and stored in an 'A(v)'. The recipe 'R(i)' must then rely
on 'A(v)'. Let this process be defined as 'interference'.

DEFINITION: Interference

    The process of 'interference' develops a recipe 'R(i)' for a mouth state
    'i' based on entry recipes 
    
                  ER = { R(i,k): k = 1...N }. 
                  
    An entry recipe 'R(i,k)' implements the concatenation of 'op(i)(R(k))'
    as it must have been computed before by accumulation. For each variable 'v'
    in 'RV(i)' it must hold:

    (i)  If all recipes in ER produce 'v' by the same procedure 'v by R(i,k)',
         then this procedure *can* be overtaken into 'R(i)'. That is,

               v in R(i) = v from R(i,k) for an arbitrary k

    (ii) Else, the value of 'v' *must* be computed upon each entry and stored
         in an auxiliary variable. The recipe 'R(i)' for 'v' becomes

               v in R(i) = A(v)

         where 'A(v)' is assigned upon each individual entry from any state 'k'
         by

              A(v) = v from R(i,k) for each k 

It is the else case in this interference procedure that induces the necessity
of multi-entry states.  Before interference can be performed, all entry
recipes must be determined.  As long as this is not the case, 'R(i)' cannot be
determined. In consequence, no successor state's recipe can be determined
through accumulation. In other words,  a mouth state blocks any propagation of
recipes as long as not all entry recipes are determined. 

The next section treats the recursive propagation of recipes by accumulation.
It is conceivable, however, that at the begin of analysis all mouth states are
undetermined. Even the initial state may be an undetermined mouth state.  In
that case, there are no springs. In that case, a so called 'dead-lock analysis'
needs to be performed. This is the subject of the next section but one.

-------------------------------------------------------------------------------

RECIPE PROPAGATION BY ACCUMULATION

The recipes for states are determined by a 'walk' along linear states. While
linear states have only one entry, they may have transitions to more than one
state. So, the walk along linear states is a recursive 'tree-walk'. The
termination criteria for the walk along linear states is defined as follows.

DEFINITION: Termination criteria for walk along linear states.

    A recursive walk along linear states does not enter the
    state ahead, if 

       (i)   there is no state. The current state is a terminal.
       (ii)  the state ahead is a mouth state.
       (iii) the state ahead is a spring.

The first condition comes natural. The second condition exists, because recipes
cannot be accumulated beyond mouth states. As a direct consequence, the walk
can never go along loops, since a loop requires a state with more than one
entry. The third condition tells that the walk stops where another walk begins
or began.  With these concepts, a first draft of an algorithm for the
determination of recipes can be defined.

          (*) Start.
          (1) springs = initial springs of state machine.
   .----->(2) perform linear walks starting from each spring.
   |          --> determine R(i) along linear states until terminal,
   |              mouth, or springs.
   |          --> entries of mouth states receive entry recipes.
   |      (3) interference in mouth states with complete sets of entry
   |          recipes.
   |      (4) springs = determined mouth states
   '- no -(5) springs empty?
          (*) Stop.

        Algorithm 1: Determination of recipes.

When this algorithm comes to an end, there might be still mouth states with
undetermined entries. The only possible reason for that are circular
dependencies between mouth states. 

PROOF: Unresolved mouth states inhibit circular dependency.

Let 

        U := set of undetermined mouth states after algorithm 1 ended.       (10)

An undetermined mouth state 'i' must have at least one undetermined entry
recipe. Thus one of its predecessor states, let it be named 'k', must be
undetermined. If 'k' is a mouth state, then it must be undetermined.  If state
'k' is a linear state, then its predecessor must be undetermined, the same
holds for k's predecessor, etc. until a mouth state is reached. Thus, the
indeterminacy of a mouth state has its reason in the indeterminacy of at least
one other mouth state--q.e.d. 

Let the fact that a mouth state 'i' is undetermined because of another undetermined
mouth state 'k' be noted as "i depends on k". 

DEFINITION: D(i) -- Dependency Set 

    For a given mouth state 'i' the dependency set 'D(i)' contains all states
    that 'i' requires to be determined, before interference in state 'i' can be
    performed.

If any state 'k' in 'D(i)' depends on another state 'p' then 'i' also depends
on it, i.e.

                   k in D(i) <=> D(k) is subset of D(i)                    (11)

The number of states in a state machine is finite, thus 'D(i)' is finite. Since
every state in 'D(i)' is undetermined, every state in 'D(i)' must depend to
another state that is undetermined. All of those states are equally in 'D(i)'.
Let the number of elements in 'D(i)' be 'n'. If the states of 'D(i)' were
displayed as dots in a plane, and the dependencies between states as arrows,
then there would be 'n' arrows between 'n' dots. This is only
possible, if there is at least one loop (proof is trivial). Thus, 

         U is not empty <=> there is at least one circular dependency      (12)

q.e.d.

It is this circular dependency which prevents algorithm 1 from being a complete
solution. The following section discusses a solution for these cases where 
the deterministic propagation of recipes failed.

-------------------------------------------------------------------------------

DEAD-LOCK STATES

Interference can only be performed, if all entry recipes of a mouth state are
determined. Loops in the state machine graph, however, cause circular
dependencies.  Figure 8 shows an example, where the two states 1 and 2 mutually
block each other. The recipe R(1) for state 1 cannot be determined because it
requires R(2) as entry recipe from state 2 which is undetermined. However,
before R(2) from state 2 can be determined, the entry recipe from
1 must be present. Both states cannot perform an interference,
because they are missing an entry recipe. 

                                       R(1)
                          R(0)     .---->----.
                    ( 0 )------>( 1 )       ( 2 )
                                   '----<----'
                                       R(2)

           Figure 8: A dead-lock in mouth states 1 and 2.

As shown, mutually obstructed interference is the reason behind dead-locks.  A
central concept for the solution is that of 'run-time interference'. It uses
the historyless recipe 'HLR(i)' for an interference in the absence of concrete
entry recipes. Using 'HLR(i)' for each undetermined entry recipe fits the
following consideration.

If a mouth state's 'op(i)' assigns a constant to a variable 'v', then the
history becomes unimportant. In that case 'v in HLV(i)'. The interference of
all entries would be a 'store/restore' if the procedure for 'v' is
inhomogeneous and it would be 'v from op(i)' if not. For each 'v not in HLV(i)'
a store/restore must be implemented at every state entry. In both cases, the
homogeneous and the inhomogeneous, the output recipe is 'A(v)' and reflects
that the value must be restored. Thus, for run-time interference an undetermined
entry from a state 'k' is assumed (not assigned) to be 

                           R(i,k) = HLR(i)


DEFINITION: Run-Time Interference

    The process of 'run-time interference' develops a recipe 'R(i)' for a mouth
    state 'i' based on an *incomplete* set of entry recipes 
    
       ER = { op(i)(R(k)): k = 1...N } where R(k) is undetermined for some 'k'. 
                  
    The entry recipes are determined by 

                       .-
                       |  v from op(i)(R(k))  if R(k) is determined
                 v  = <
                       |  A(v)                if R(k) is undetermined
                       '-

    With all entries 'R(i,k)' specified, the output recipe 'R(i)' is determined
    as with normal interference.

The run-time interference is correct if and only if the entry recipes are
correct. If the output of a recipe of a mouth state is correct, then all
recipes derived from its accumulation are correct. This is so, since
accumulation is deterministic, without any run-time dependency. To proof the
correctness of run-time interference, the term 'horizon' is defined.

DEFINITION: Horizon

   Let the term 'horizon' H indicate the set of dead-lock mouth states that
   have at least one determined entry.

The name 'horizon' is chosen because it defines the border of determination.
Beyond that begins the realm of dead-locks. Figure 9 shows a horizon state
which contains one determined entry and another undetermined entry.

                       R(i,a) -->--.
                                    \
                                   ( i )----> R(i)
                                    /
                   R(i,b) = ? -->--'

          Figure 9: A mouth state with a fix entry recipe R(x,a).

Every undetermined entry has its origin in a mouth state that is unable to
perform interference. Every determined entry has its origin either in the
initial state, or a mouth state that performed interference. Interference
happens only if all entries are determined. Thus, any mouth state that performs
interference finally has its roots in the initial state. As a consequence, the
following statement can be made.

STATEMENT: 

   A dead-lock states can only reached by a path that guides through a horizon
   state. 

In other words, the horizon states are the entry points to the realm of
dead-lock states.  The entry into the horizon state happens through the
determined entry--in the example of figure 9 it is 'R(i,a)'. Computing and
storing the value for each variable is correct, at this point in time, since
the entry recipe is derived by deterministic procedures. Thus, restoring the
stored values is a correct procedure to determine the DCV.  'R(i)' is correct,
at the time of entry into a horizon. Accumulation along linear states is
deterministic. A propagated recipe 'R(i)' results in correct entries to
other mouth states, run-time interference produces again a correct
output recipe and the discussion continues where it started.  It follows
the following statement.

STATEMENT:

   Repeated run-time interference and accumulation of resulting recipes results
   in a correct description of the state machine in terms of recipes.

The problem of dead-locks is, hereby, solved. All states are associated with
recipes and the original operations along the transitions are no longer
required.

-------------------------------------------------------------------------------

FINE TUNING OF DEAD-LOCK STATES

While the previous discussion provides a complete solution, there is still
space for improvement. Figure 10 shows a case where the DCV variable 'x' is
assigned 5 upon entry into state 1 in any case. Storing the value upon entry
and restoring it upon exit, is superfluous. Since the entry recipes are
homogeneous, normal interference may be applied. For the entry from state 1
into state 2, the recipe 'x=6' is sufficient. This section discusses how normal
interference may be applied to further simplify the description while
maintaining correctness.

                                       x=x+1
                          x=5      .---->----.
                    ( 0 )------>( 1 )       ( 2 )
                                   '----<----'
                                       x=5

          Figure 10: Dead-lock group with space for improvement.


By definition, run-time interference can only happen in a state with at least
one determined entry recipe.  Algorithm 1 applied a procedure based on the
deterministic accumulation and interference. Thus, any recipe that resulted
from algorithm 1 is stable and correct.  

In figure 9 a horizon state is shown. Without restricting generality, the entry
recipe 'R(i,b)' represents all inputs into the state which are undetermined
before dead-lock resolution. In the same sense 'R(i,a)' represents all
determined entries. For interference to happen, it must hold

      R(i,a) = R(i,b) with a, b in the set of entry states to state i.

Such is the requirement of homogeneity. The recipe 'R(i,a)' can only depend on
states before the horizon. If it is equal to a recipe 'R(i,b)', then this
recipe also can only depend on states before the horizon. Thus, while 'R(i,b)'
results from interferences and accumulation inside the realm of dead-lock
states, it does not depend on its 'dynamics'. According to the previous
discussion 'R(i,b)' is correct in the general sense. Thus, the derivation
of a resulting recipe is correct and stable in a general sense. 

STATEMENT:

    If entries into a horizon state are homogeneous, then the recipe resulting
    from interference is correct in a general sense. No feedback into the mouth
    state must be further considered. The resulting recipe remains stable.

The output recipe 'R(i)' of the horizon state is determined and correct. After
interference, such a mouth state is no longer part of the horizon. However,
through accumulation of 'R(i)' some other dead-lock mouth states may be
reached. They now have a determined recipe at their entry and become new
horizon states. The procedure of interference and accumulation may be repeated
until no new horizon states with homogeneous entries are found.

-------------------------------------------------------------------------------

