import quex.engine.generator.state.transition_map.solution  as solution

class Bisection(object):
     __slots__ = ("bisection_value", "low", "high")
     def __init__(self, BisectionValue, Low, High):
         """TM -- transition map
            MOAT -- Most Often Appearing Target
         """
         self.bisection_value = BisectionValue
         self.low             = Low
         self.high            = High

    def implement(self):
        txt = [
            Lng.IF_INPUT("<", self.bisection_value)
        ]
        txt.extend(
            self.lower.implement()
        )
        txt.append(
            Lng.ELSE
        )
        txt.extend(
            self.higher.implement()
        )
        txt.append("\n")
        return txt
