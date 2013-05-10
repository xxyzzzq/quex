from   quex.engine.interval_handling import Interval
from   quex.blackboard import E_StateIndices, E_ActionIDs
from   quex.engine.tools import r_enumerate
from   quex.blackboard   import E_StateIndices

from   copy import deepcopy, copy
from   itertools import izip
import sys

class TransitionMap(list):
    """________________________________________________________________________
    A TransitionMap is a list of pairs:

                [ [ interval_0, target_0],
                  [ interval_1, target_1],
                  ...
                  [ interval_N, target_N] ]

    where the intervals are sorted and non-overlapping. Drop-out intervals 
    are best associated with a target == E_StateIndices.DROP_OUT.

    NOTE: len(self) == 0 indicates: empty transition map.
    ___________________________________________________________________________
    """
    @classmethod
    def from_TargetMap(cls, TM):
        result = cls()
        for target, character_set in TM.get_map().iteritems():
            assert not character_set.is_empty()
            result.extend((interval.clone(), target) 
                        for interval in character_set.get_intervals(PromiseToTreatWellF=True))
        result.sort()
        # Empty transition maps shall not fill their gaps!
        if len(result) != 0:
            result.fill_gaps(E_StateIndices.DROP_OUT)
        return result

    @classmethod
    def from_iterable(cls, Iterable, TargetFactory=deepcopy):
        result = cls()
        result.extend((interval.clone(), TargetFactory(target)) 
                      for interval, target in Iterable)
        return result

    @staticmethod
    def izip(TransitionMapA, TransitionMapB):
        """Produces an iterable over two transition maps at once. The borders in the
        zipped transition map consist of a superset of all borders of transition
        map 'A' and 'B'. Whenever a border hits a new interval is notified. 

                YIELDS:  begin, end, a_target, b_target

        Interval [begin, end) is homogenous in the zipped transition map, i.e.
        inside this interval 'A' triggers to 'a_target' and 'B' to 'b_target'.  

        NOTE: The name is derived from python's 'itertools.izip'.
        """
        assert len(TransitionMapA) != 0 
        assert TransitionMapA[0][0].begin == - sys.maxint
        assert TransitionMapA[-1][0].end  == sys.maxint
        assert len(TransitionMapB) != 0 
        assert TransitionMapB[0][0].begin == - sys.maxint
        assert TransitionMapB[-1][0].end  == sys.maxint

        LenA             = len(TransitionMapA)
        LenB             = len(TransitionMapB)
        i                = 0 # iterator over TransitionMapA
        k                = 0 # iterator over TransitionMapB
        i_itvl, i_target = TransitionMapA[i]
        k_itvl, k_target = TransitionMapB[k]
        prev_end         = - sys.maxint
        # Intervals in trigger map are always adjacent, so the '.begin' member is
        # not accessed.
        while not (i == LenA - 1 and k == LenB - 1):
            end    = min(i_itvl.end, k_itvl.end)

            yield prev_end, end, i_target, k_target

            prev_end  = end

            if   i_itvl.end == k_itvl.end: 
                i += 1; i_itvl, i_target = TransitionMapA[i]
                k += 1; k_itvl, k_target = TransitionMapB[k]
            elif i_itvl.end <  k_itvl.end: 
                i += 1; i_itvl, i_target = TransitionMapA[i]
            else:                          
                k += 1; k_itvl, k_target = TransitionMapB[k]

        # Treat the last trigger interval
        yield prev_end, sys.maxint, TransitionMapA[-1][1], TransitionMapB[-1][1]
        return

    def clone(self):
        return self.from_iterable(self)

    def relate_to_door_ids(self, TheAnalyzer, StateIndex):
        """Creates a transition_map that triggers to DoorIDs instead of target states.
        """
        def relate(Target):
            if Target == E_StateIndices.DROP_OUT:
                return Target
            else:
                result = TheAnalyzer.state_db[Target].entry.get_door_id(StateIndex=Target, FromStateIndex=StateIndex)
                return result
        
        return self.__class__.from_iterable(self, relate)

    def get_target(self, Character):
        i = self.bisect(Character)
        if i is None: return None
        return self[i][1]

    def set_target(self, Character, NewTarget):
        i = self.bisect(Character)
        if i is None:
            self.insert(0, (Interval(Character), NewTarget))
            self.sort()
            return

        interval, target = self[i]

        # Found the interval that contains the Character
        assert interval.size() > 0
        L = len(self)

        # Check whether an adjacent interval has the same target, so that
        # the new interval can directly be docked to it.
        if target == NewTarget:
            return # Nothing to be done

        if interval.size() == 1:
            if i > 0 and interval.begin == Character and self[i-1][1] == NewTarget:
                # Interval before fits
                if i < L-1 and interval.end == Character + 1 and self[i+1][1] == NewTarget:
                    # Interval before and after fits
                    self[i-1][0].end = self[i+1][0].end
                    del self[i:i+2]
                else:
                    # Only interval before fits
                    self[i-1][0].end = self[i][0].end
                    del self[i]

            elif i < L-1 and interval.end == Character + 1 and self[i+1][1] == NewTarget:
                # Only interval after fits, Interval before does not fit
                self[i+1][0].begin = self[i][0].begin
                del self[i]

            else:
                self[i] = (interval, NewTarget)

            self.assert_continuity()
            return

        if i > 0 and interval.begin == Character and self[i-1][1] == NewTarget:
            # Interval before fits, Interval after cannot fit, because size() > 1
            self[i-1][0].end = Character + 1
            self[i][0].begin = Character + 1

        elif i < L-1 and interval.end == Character + 1 and self[i+1][1] == NewTarget:
            # Interval after fits, Interval before cannot fit, because size() > 1
            self[i+1][0].begin = Character 
            self[i][0].end     = Character

        elif interval.begin == Character:
            self[i][0].begin = Character + 1
            self.insert(i, (Interval(Character), NewTarget))

        elif interval.end == Character + 1:
            self.insert(i+1, (Interval(Character), NewTarget))
            self[i][0].end = Character

        else:
            # Character lies in the middle of a non-fitting interval
            self.insert(i+1, (Interval(Character), NewTarget))
            self.insert(i+2, (Interval(Character+1, interval.end), target))
            self[i][0].end = Character 

        self.assert_continuity()
        return

    def has_action_id(self, ActionID):
        for interval, action in self:
            if type(action) == list and ActionID in action:
                return True
            elif action == ActionID:
                return True
        return False

    def replace_action_id(self, ActionID, Action):
        assert ActionID in E_ActionIDs
        assert Action is None or type(Action) == list

        for interval, action in self:
            try:    idx = action.index(ActionID)
            except: continue

            del action[idx]
            
            if Action is None: continue

            for x in Action:
                action.insert(idx, x)
                idx += 1
        return

    def delete_action_ids(self):
        for interval, action in self:
            if type(action) != list: continue
            i = len(action) - 1
            while i >= 0:
                if action[i] in E_ActionIDs:
                    del action[i]
                i -= 1
        return

    def insert_after_action_id(self, ActionID, Action):
        assert ActionID in E_ActionIDs
        assert Action is None or type(Action) == list

        if Action is None:
            return

        done_set = set()
        for interval, action in self:
            if id(action) in done_set: continue
            done_set.add(id(action))

            try:    idx = action.index(ActionID)
            except: continue

            for x in Action:
                idx += 1
                action.insert(idx, x)
        return

    def combine_adjacents(self):
        L = len(self) 
        if L == 0: return
        prev_interval, prev_target = self[L-1]
        for i in reversed(xrange(L-1)):
            interval, target = self[i]
            if interval.end == prev_interval.begin and prev_target == target:
                interval.end = prev_interval.end
                del self[i+1]
            else:
                prev_target   = target
            prev_interval = interval

    def sort(self):
        list.sort(self, key=lambda x: (x[0].begin, x[0].end))

        # double check -- no overlapping!
        if len(self) != 0:
            prev_interval = self[0][0]
            for interval, target in self[1:]:
                assert interval.begin >= prev_interval.end

    def clean_up(self):
        """NOTE: 'clean_up()' does not mean that there are no gaps! For that
                 consider '.combine_adjacents()' or '.fill_gaps()'
        """
        self.sort()
        self.combine_adjacents()

    def index(self, Character):
        """Searches for interval that contains 'Character' and returns
           the index in the transition map to the corresponding entry.

           RETURNS: None      -- Character not found
                    index > 0 -- where interval 'self[i][0]' contains Character.
        """
        return self.bisect(Character)

    def smoothen(self, Character):
        """Replaces a single character transition by a transition of its adjacent 
        intervals.
        """
        i = self.index(Character)
        assert self[i][0].size() == 1

        L = len(self)
        if i > 0: 
            if i < L - 1 and self[i+1][1] == self[i-1][1]:
                self[i-1][0].end = self[i+1][0].end
                del self[i:i+2]
            else:
                self[i-1][0].end = Character
                del self[i]

        elif i < L:
            self[i+1][0].end = Character + 1
            del self[i]
        else:
            assert False

    def is_equal(self, Other):
        if len(self) != len(Other): return False
        for x, y in izip(self, Other):
            if   x[0] != y[0]: return False  # Interval
            elif x[1] != y[1]: return False  # Target
        return True

    def fill_gaps(self, Target):
        """Fill gaps in the transition map. 
        """
        size = len(self)

        if size == 0:
            self.append((Interval(-sys.maxint, sys.maxint), Target))
            return

        # If outer borders are lacking, then add them
        if self[0][0].begin != -sys.maxint: 
            self.insert(0, (Interval(-sys.maxint, self[0][0].begin), Target))
            size += 1

        if self[-1][0].end != sys.maxint: 
            self.append((Interval(self[-1][0].end, sys.maxint), Target))
            size += 1

        # Fill gaps between the intervals
        prev_end    = self[0][0].end
        prev_target = self[0][1]
        i           = 1
        while i < size:
            interval = self[i][0]
            target   = self[i][1]


            ##print 
            ##print "#i:", i
            ##print "#tm:", self
            ##print "#int,target:", interval, target
            ##print "#prev_end, prev_target:", prev_end, prev_target
            assert interval.begin != interval.end
            assert interval.begin >= prev_end

            if prev_end == interval.begin: 
                ##print "#A"
                if prev_target == target:
                    # (*) Combine two intervals which have the same target
                    self[i-1][0].end = interval.end
                    del self[i]
                    size -= 1
                else:
                    i += 1
                prev_end    = interval.end
                prev_target = target

            elif prev_target != Target:
                ##print "#B"
                # (*) Gap detected, targets differ => fill!
                self.insert(i, (Interval(prev_end, interval.begin), Target))
                size += 1
                # prev_target = same;
                # prev_end    = same; 
                # NOT: i+=1, because need to check for combination with next interval.

            else:
                ##print "#C", prev_target, Target
                # (*) Gap detected, targets equal => extend!
                self[i-1][0].end = interval.begin
                prev_target = Target
                prev_end    = interval.begin
                # NOT: i+=1, because need to check for combination with next interval.

    def cut(self, CharacterSet):
        result = []
        for interval, target in self:
            diff = CharacterSet.intersection(interval)
            result.extend((x_interval, target) 
                          for x_interval in diff.get_intervals(PromiseToTreatWellF=True))
        return result

    def bisect(self, Character):
        lower = 0
        upper = len(self)
        if upper == 0:
            return None

        while upper - lower > 1:
            i = (upper + lower) >> 1
            if   self[i][0].begin >  Character: upper = i
            elif self[i][0].end   <= Character: lower = i
            else:                                         return i

        if     Character >= self[lower][0].begin \
           and Character <  self[lower][0].end:
            return lower

        return None

    def fill_empty_actions(self, TransitionActionMap):
        return self.add_transition_actions(TransitionActionMap, OnlyIfEmptyF=True)

    def add_action_to_all(self, Action):
        assert isinstance(Action, list)
        done_set = set()
        for interval, action in self:
            if id(action) in done_set: continue
            done_set.add(id(action))
            action.extend(Action)

    def add_transition_actions(self, TransitionActionMap, OnlyIfEmptyF=False):
        """'TransitionActionMap' describes actions to be taken upon the occurence
        of a particular character.  The actions are to be added to the
        'self'.  
        """
        def extend(Target, ActionList, OnlyIfEmptyF):
            if isinstance(Target, (int, long)) or Target in E_StateIndices:
                return Target
            elif len(Target) == 0:
                return copy(ActionList)
            elif OnlyIfEmptyF:
                return copy(Target)

            result = copy(Target)
            if len(Target[-1]) != 0:
                plain_target = Target[-1][-1].rstrip()
                if len(plain_target) and plain_target[-1] == "\n": result.append(0)
            result.extend(ActionList)
            return result

        result = []
        for begin, end, target, action_list in TransitionMap.izip(self, TransitionActionMap):
            if action_list is None:
                result.append((Interval(begin, end), copy(target)))
            else:
                result.append((Interval(begin, end), extend(target, action_list, OnlyIfEmptyF)))
        return result

    def prune(TriggerMap, Begin, End):
        """Consider the 'useful range' starting from zero. Thus, the first 
           interval to be considered is the first that intersects with 0.
           Then 'begin' must become '0' instead of a negative value.
        """
        L = len(TriggerMap)

        # Iterate from 'low' to 'high'
        begin_i = None
        for i, info in enumerate(TriggerMap):
            interval, target = info
            if interval.end <= Begin: continue

            # Found an interval that intersects with 'Begin' line
            if interval.begin < Begin:
                interval.begin = Begin
            begin_i = i
            break

        if begin_i is None: del TriggerMap[:] # No element is in range
        elif begin_i != 0:  del TriggerMap[:begin_i]

        # Iterate from 'high' to 'low'
        end_i = None
        for i, info in r_enumerate(TriggerMap):
            interval, target = info
            if interval.begin > End: continue

            # Found an interval that intersects with 'End' line
            if interval.end > End:
                interval.end = End 

            end_i = i
            break

        if   end_i is None: del TriggerMap[:] # No element in range
        elif end_i != L-1:  del TriggerMap[end_i+1:]

        # Delete all intervals which have become empty
        i    = 0
        size = len(TriggerMap)
        while i < size:
            if TriggerMap[i][0].begin == TriggerMap[i][0].end:
                del TriggerMap[i]
                size -= 1
            else:
                i += 1

        return

    def assert_no_empty_action(self):
        for interval, action in self:
            assert action is not None
            assert not isinstance(action, list) or len(action) != 0

    def assert_continuity(self, StrictF=True):
        """StrictF => Assume that adjacent intervals have been combined. 

           Tests that all intervals appear in a sorted manner.

           NOTE: 'assert_adjacency' is stronger than 'assert_continuity'. 
                 It is not necessary to test for both. Rather decide what
                 level needs to be asserted.
        """
        if len(self) == 0:
            return 

        iterable                   = self.__iter__()
        prev_interval, prev_target = iterable.next()
        # No 'empty' intervals
        assert prev_interval.end > prev_interval.begin

        for interval, target in iterable:
            assert interval.end > interval.begin        # No empty intervals
            assert interval.begin >= prev_interval.end  # Intervals appear sorted, 
            if interval.begin == prev_interval.end and StrictF:
                # If the touch, require the target is different
                assert target != prev_target
            prev_interval = interval
            prev_target   = target

    def assert_adjacency(self, TotalRangeF=False, ChangeF=False):
        """Check that the trigger map consist of sorted adjacent intervals 
           This assumption is critical because it is assumed that for any isolated
           interval the bordering intervals have bracketed the remaining cases!
        """
        if len(self) == 0: 
            assert not TotalRangeF
            return

        if TotalRangeF: 
            assert self[0][0].begin == -sys.maxint
            assert self[-1][0].end  == sys.maxint

        iterable    = self.__iter__()
        info        = iterable.next()
        prev_end    = info[0].end
        prev_target = info[1]

        for interval, target in iterable:
            assert interval.end > interval.begin        # No empty intervals

            # Intervals are adjacent!
            assert interval.begin == prev_end, \
                   "interval.begin: 0x%X != prev_end: 0x%X" % (interval.begin, prev_end)
            # Interval size > 0! 
            assert interval.end   > interval.begin, \
                   "interval.end: %x <= interval.begin: 0x%X" % (interval.end, interval.begin)
            if ChangeF:
                assert target != prev_target 

            prev_end    = interval.end
            prev_target = target

        # If we reach here, then everything is OK.
        return

    def get_string(self, Option="utf8", IntervalF=True):
        assert Option in ("hex", "dec", "utf8")
        def get(X):
            if   X == sys.maxint:   return "+oo"
            elif X == - sys.maxint: return "-oo"
            return "%i" % X
        if len(self) == 0:
            return "   <empty>"
        L = max(len(x[0].get_string(Option)) for x in self)
        txt = []
        for interval, target in self:
            if IntervalF: interval_str = interval.get_string(Option)
            else:         interval_str = "[%s:%s)" % (get(interval.begin), get(interval.end))
            txt.append("   %s%s %s\n" % (interval_str, " " * (L - len(interval_str)), target))
        return "".join(txt)

