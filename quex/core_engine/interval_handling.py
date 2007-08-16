#! /usr/bin/env python
# PURPOSE: Provides classes for handling of sets of numbers:
#
#     Interval: A continous set of numbers in a range from a
#              minimum to a maximum border.
# 
#     NumberSet: A non-continous set of numbers consisting of
#                described as a set of intervals.
#
# DATE: May 26, 2006
#
# (C) 2006 Frank-Rene Schaefer
#
# ABSOLUTELY NO WARRANTY
################################################################################

from copy import copy, deepcopy
from quex.frs_py.string_handling import blue_print

import quex.core_engine.generator.languages.core as languages
import quex.core_engine.utf8                     as utf8
import sys

class Interval:
    """Representing an interval with a minimum and a maximum border. Implements
    basic operations on intervals: union, intersection, and difference.
    """
    def __init__(self, Begin=None, End=None):
        """NOTE: Begin = End signifies **empty** interval.

        Begin == None and End == None   => Empty Interval

        Begin == int and End == None    => Interval of size '1' (one number = Begin)
        
        Begin and End != None           => Interval starting from 'Begin' and the last
                                           element is 'End-1'

        """

        # .begin = smallest integer that belogns to interval.
        # .end   = first integer > 'Begin' that does **not belong** to interval
        if Begin == None and End == None:
            # empty interval
            self.begin = 0
            self.end   = 0
        else:
            if Begin == None:
                raise "Begin can only be 'None', if End is also 'None'!"
            self.begin = Begin            
            if End == None:  
                if self.begin != sys.maxint: self.end = self.begin + 1
                else:                        self.end = self.begin
            else:    
                self.end = End
            
    def is_empty(self):
        return self.begin == self.end

    def is_all(self):
        return self.begin == -sys.maxint and self.end == sys.maxint   
        print "##res:", result
 
    def contains(self, Number):
        """True  => if Number in NumberSet
           False => else
        """
        if Number >= self.begin and Number < self.end: return True
        else:                                          return False
        
    def check_overlap(self, Other):
        """Does interval overlap the Other?"""
        def helper(A, B):
            """HELPER: Tests for overlap (half way through). In order to measure
            overlap this function must be called twice:
                     __overlap(X, Y) and __overlap(Y, X)"""        
            if A.begin < B.end and A.end > B.begin: return True
            else:                                   return False
            
        return helper(self, Other) or helper(Other, self)

    def check_touch(self, Other):
        """Does interval touch the Other?"""
        return self.check_overlap(Other) \
               or self.begin == Other.begin or self.end == Other.begin
    
    def union(self, Other):
        if self.check_overlap(Other):
            # overlap: return one single interval
            #          (the one that encloses both intervals)
            return [ Interval(min(self.begin, Other.begin),
                              max(self.end, Other.end)) ]
        else:
            # no overlap: two disjunct intervals
            result = []
            if not self.is_empty(): result.append(copy(self))
            if not Other.is_empty(): result.append(copy(Other))
            return result

    def intersection(self, Other):
        if self.check_overlap(Other):
            # overlap: return one single interval
            #          (the one that both have in common)
            return Interval(max(self.begin, Other.begin),
                            min(self.end, Other.end)) 
        else:
            # no overlap: empty interval (begin=end)
            return Interval()  # empty interval

    def difference(self, Other):
        """Difference self - Other."""
        if self.begin >= Other.begin:
            if self.end <= Other.end:
                # overlap: Other covers self
                # --------------[xxxxxxxxxxxxx]-------------------
                # ---------[yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy]-----
                #
                #          nothing remains - empty interval
                return []
            else:
                if self.begin >= Other.end:
                    # no intersection
                    return [ copy(self) ]
                else:
                    # overlap: Other covers lower part
                    # --------------[xxxxxxxxxxxxxxxxxxxx]------------
                    # ---------[yyyyyyyyyyyyyyyyyyyy]-----------------
                    return [ Interval(Other.end, self.end) ]
        else:            
            if self.end >= Other.end:
                # overlap: self covers Other
                # ---------[xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx]-----
                # --------------[yyyyyyyyyyyyy]-------------------
                #
                # result = two disjunct intervals
                result = []
                lower_part = Interval(self.begin, Other.begin)
                if not lower_part.is_empty(): result.append(lower_part)
                upper_part = Interval(Other.end, self.end)
                if not upper_part.is_empty(): result.append(upper_part)
                return result
            else:
                if self.end <= Other.begin:
                    # no intersection
                    return [ copy(self) ]
                else:
                    # overlap: Other upper part
                    # ---------[xxxxxxxxxxxxx]------------------------
                    # --------------[yyyyyyyyyyyyy]-------------------
                    #                
                    return [ Interval(self.begin, Other.begin) ]

    def inverse(self):
        if self.begin == self.end:
            # empty interval => whole range
            return [ Interval(-sys.maxint, sys.maxint) ]
        else:
            result = []
            if self.begin != -sys.maxint: result.append(Interval(-sys.maxint,self.begin))
            if self.end   != sys.maxint:  result.append(Interval(self.end, sys.maxint))
            return result

    def __repr__(self):
        return "[" + repr(self.begin) + ", " + repr(self.end) + ")"

    def get_utf8_string(self):
        #_____________________________________________________________________________
        if self.begin > self.end:
            raise "Begin of interval '%i' lies behind end of interval '%i'." % (self.begin, self.end)
        
        def utf8_char(Code):
            if   Code == - sys.maxint:   return "-oo"
            elif Code == sys.maxint:     return "oo"            
            elif Code == ord('\n'):      return "'\\n'"
            elif Code == ord('\t'):      return "'\\t'"
            elif Code == ord('\r'):      return "'\\r'"
            elif Code < ord('0'):        return "\\" + repr(Code) 
            else:
                char_str = utf8.map_unicode_to_utf8(Code)
                return "'" + char_str + "'"
            # elif Code < ord('0') or Code > ord('z'): return "\\" + repr(Code)
            # else:                                    return "'" + chr(Code) + "'"

        if self.begin == self.end: 
            return "''"
        elif self.end - self.begin == 1: 
            return utf8_char(self.begin) 
        else:                          
            if   self.end == -sys.maxint: end_char = "-oo"
            elif self.end == sys.maxint:  end_char = "oo"
            else:                         end_char = utf8_char(self.end-1)
            return "[" + utf8_char(self.begin) + ", " + end_char + "]"

    def gnuplot_string(self, y_coordinate):
        if self.begin == self.end: return ""
        txt = ""
        txt += "%i %f\n" % (self.begin, y_coordinate)
        txt += "%i %f\n" % (self.end-1, y_coordinate)
        txt += "%i %f\n" % (self.end-1, float(y_coordinate) + 0.8)
        txt += "%i %f\n" % (self.begin, float(y_coordinate) + 0.8)
        txt += "%i %f\n" % (self.begin, y_coordinate)
        return txt

            
class NumberSet:
    """Represents an arbitrary set of numbers. The set is described
       in terms of intervals, i.e. objects of class 'Interval'. This
       class also provides basic operations such as union, intersection,
       and difference.
    """
    
    def __init__(self, Arg = None):
        """Arg = list     ==> list of initial intervals
           Arg = Interval ==> initial interval
           Arg = integer  ==> interval consisting of one number
           """
        self.__intervals = []
        
        if type(Arg) == list:
            # use 'add_interval' to ensure consistency
            for interval in Arg:
                if interval.__class__.__name__ != "Interval":
                    raise "list contained object of type %s\nexpected 'Interval'" % \
                          interval.__class__.__name__
                self.add_interval(deepcopy(interval))

        elif Arg.__class__.__name__ == "Interval":
            self.add_interval(deepcopy(Arg))

        elif Arg.__class__.__name__ == "NumberSet":
            self.__intervals = deepcopy(Arg.__intervals)

        elif type(Arg) == int:
            self.add_interval(Interval(Arg))

        elif Arg != None:
            # Arg == -1 => empty number set
            raise "error: no way to handle Arg = ", repr(Arg)

    def add_interval(self, NewInterval):
        """Adds an interval and ensures that no overlap with existing
        intervals occurs. Note: the 'touch' test is faster here, because
        only one interval is checked against. Do not use __touchers()!"""
        if NewInterval.is_empty(): return
        
        # (1) determine if begin overlaps with the new interval
        toucher_list = [] 
        for interval in self.__intervals:
            if interval.check_touch(NewInterval):
                toucher_list.append(interval)

        # (2) combine all intervals that intersect with the new one
        min_begin = NewInterval.begin
        max_end   = NewInterval.end
        for toucher in toucher_list:
            if toucher.begin < min_begin: min_begin = toucher.begin
            if toucher.end > max_end:     max_end   = toucher.end
        combination = Interval(min_begin, max_end)

        # (3) build new list of intervals
        #     (all overlaps are deleted, i.e. not added because they are
        #      replaced by the union with the NewInterval)
        new_interval_list = [ combination ]
        for interval in self.__intervals:
            if interval not in toucher_list:
                new_interval_list.append(interval)

        self.__intervals = new_interval_list
        self.clean()

    def cut_interval(self, CutInterval):
        """Cuts an interval from the intervals of the set.
        Note: the 'overlap' test is faster here, because
        only one interval is checked against. Do not use __overlapers()!"""
        
        # (1) deterbegine overlaps with the cutting interval
        overlapper_list = [] 
        for interval in self.__intervals:
            if interval.check_overlap(CutInterval):
                overlapper_list.append(interval)

        # (2) substract NewInterval from all intervals that overlap
        combination = CutInterval
        for overlapper in overlapper_list:
            difference_interval = overlapper.substract(CutInterval)
            combination.append(difference_interval)

        # (3) build new list of intervals
        #     (all overlaps are deleted, i.e. not added because they are
        #      replaced by the union with the CutInterval)
        new_interval_list = combination
        for interval in self.__intervals:
            if interval not in overlapper_list:
                new_interval_list.append(interval)

        self.__intervals = new_interval_list
        self.clean()

    def contains(self, Number):
        """True  => if Number in NumberSet
           False => else
        """
        for interval in self.__intervals:
            if interval.contains(Number): return True
        return False

    def is_empty(self):
        if self.__intervals == []: return True
        for interval in self.__intervals:
            if interval.is_empty() == False: return False
        return True
        
    def is_all(self):
        """Returns True if this NumberSet covers all numbers, False if not.
           
           Note: All intervals should have been added using the function 'add_interval'
                 Thus no overlapping intervals shall exists. If the set covers all numbers,
                 then there can only be one interval that 'is_all()'
        """
        if len(self.__intervals) != 1: return False
        return self.__intervals[0].is_all()
            
    def interval_number(self):
        """This value gives some information about the 'complexity' of the number set."""
        return len(self.__intervals)

    def get_intervals(self):
        return deepcopy(self.__intervals)

    def union(self, Other):
        if Other.__class__.__name__ == "Interval": Other = NumberSet(Other)

        shadow_of_self = deepcopy(self)
        # simply add all intervals to one single set
        for interval in Other.__intervals + shadow_of_self.__intervals:
            shadow_of_self.add_interval(interval)
        return shadow_of_self            

    def intersection(self, Other):
        if Other.__class__.__name__ == "Interval": Other = NumberSet(Other)

        # intersect with each interval
        result = NumberSet()
        for interval in Other.__intervals:
            for my_interval in self.__intervals:
                intersection = my_interval.intersection(interval)
                if intersection != None:
                    result.add_interval(intersection)

        return result

    def difference(self, Other):
        if Other.__class__.__name__ == "Interval": Other = NumberSet(Other)

        if self.__overlappers() != []:
            raise "NumberSet::difference() expects non-overlapping intervals"
        
        # note: there should be no overlaps according to 'add_interval'
        remainder = deepcopy(self)
        for interval in Other.__intervals:
            new_remainder = NumberSet()
            for my_interval in remainder.__intervals:
                subtraction = my_interval.difference(interval)
                for sub_interval in subtraction:
                    new_remainder.add_interval(sub_interval)
            remainder = new_remainder
        return remainder

    def inverse(self):
        """Intersection of inverses of all intervals."""
        inverse_intervals = []

        result = NumberSet(Interval(-sys.maxint, sys.maxint))
        i = -1        
        for interval in self.__intervals:
            inv_interval = interval.inverse()
            result = result.intersection(NumberSet(inv_interval))

        return result
        
    def clean(self):
        """Sorts all intervals, so according to their beginimum. Lowest comes first."""

        # sort all intervals
        self.__intervals.sort(lambda a, b: -cmp(b.begin, a.begin))        

    def __overlappers(self):
        tmp = {} # use this to get unique values of indices
        #        # tmp.values() == indices of intervals that overlap
        for i in range(len(self.__intervals)):
            for k in range(i):
                if self.__intervals[i].check_overlap(self.__intervals[k]):
                    tmp[i] = 1
                    tmp[k] = 1
        return map(lambda idx: self.__intervals[idx], tmp.values())

    def __touchers(self):
        tmp = {} # use this to get unique values of indices
        #        # tmp.values() == indices of intervals that touch
        for i in range(len(self.__intervals)):
            for k in range(i):
                if self.__intervals[i].check_touch(self.__intervals[k]):
                    tmp[i] = 1
                    tmp[k] = 1
        return map(lambda idx: self.__intervals[idx], tmp.values())

    def __repr__(self):
        return repr(self.__intervals)

    def get_utf8_string(self):
        msg = ""
        for interval in self.__intervals:
            msg += interval.get_utf8_string() + ", "
        if msg != "": msg = msg[:-2]
        return msg

    def gnuplot_string(self, y_coordinate):
        txt = ""
        for interval in self.__intervals:
            txt += interval.gnuplot_string(y_coordinate)
            txt += "\n"
        return txt

    def condition_code(self,
                       Language     = "C",
                       FunctionName = "example"):

        LanguageDB = languages.db[Language]
        txt  = LanguageDB["$function_def"].replace("$$function_name$$", FunctionName)
        txt += self.__condition_code(LanguageDB)
        txt += LanguageDB["$function_end"]

        return txt

    def __condition_code(self, LanguageDB,
                         LowestInterval_Idx = -1, UppestInterval_Idx = -1, 
                         NoIndentF = False):
        
        """Writes code that does a mapping according to 'binary search' by
        means of if-else-blocks.
        """
        if LowestInterval_Idx == -1 and UppestInterval_Idx == -1:
            LowestInterval_Idx = 0
            UppestInterval_Idx = len(self.__intervals) - 1
            
        if NoIndentF:
            txt = ""
        else:
            txt = "    "

        MiddleInterval_Idx = (UppestInterval_Idx + LowestInterval_Idx) / 2
        
        # quick check:
        if UppestInterval_Idx < LowestInterval_Idx:
            raise "NumberSet::conditions_code(): strange interval indices:" + \
                  "lowest interval index = " + repr(LowestInterval_Idx) + \
                  "uppest interval index = " + repr(UppestInterval_Idx)
        
        middle = self.__intervals[MiddleInterval_Idx]
        
        if LowestInterval_Idx == UppestInterval_Idx \
           and middle.begin == middle.end - 1:
            # middle == one element
            txt += "$if input $== %s $then\n" % repr(middle.begin)
            txt += "    $return_true\n"
            txt += "$end\n"
            txt += "$return_false\n"
            
        else:
            # middle interval > one element
            txt += "$if input $>= %s $then\n" % repr(middle.end)

            if MiddleInterval_Idx == UppestInterval_Idx:
                # upper interval = none
                txt += "    $return_false\n"
                txt += "$end\n"
            else:
                # upper intervals = some
                txt += self.__condition_code(LanguageDB,
                                             MiddleInterval_Idx + 1, UppestInterval_Idx)
                txt += "$end\n"

            txt += "$if input $>= %s $then\n" % repr(middle.begin)
            txt += "    $return_true\n"
            txt += "$end\n" 

            if MiddleInterval_Idx == LowestInterval_Idx:
                # lower intervals = none
                txt += "$return_false\n"
            else:
                # lower intervals = some
                txt += self.__condition_code(LanguageDB,
                                             LowestInterval_Idx, MiddleInterval_Idx - 1,
                                             NoIndentF = True)
            
        # return program text for given language
        return languages.replace_keywords(txt, LanguageDB, NoIndentF)

