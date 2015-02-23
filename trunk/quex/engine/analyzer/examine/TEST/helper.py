from quex.engine.analyzer.examine.state_info import *
from quex.engine.analyzer.examine.acceptance import *
from quex.engine.operations.se_operations    import SeAccept, SeStoreInputPosition
from quex.engine.misc.tools                  import flatten_list_of_lists
from quex.blackboard                         import E_PreContextIDs, E_R, E_IncidenceIDs

from copy import deepcopy, copy
from itertools import izip

def get_SeAccept(AcceptanceId, PreContextId=E_PreContextIDs.NONE, RestorePositionF=False):
    cmd = SeAccept()
    cmd.set_acceptance_id(AcceptanceId)
    cmd.set_pre_context_id(PreContextId)
    if RestorePositionF:
        cmd.set_restore_position_register_f()
    return cmd

def add_SeAccept(sm, StateIndex, AcceptanceId, PreContextId=E_PreContextIDs.NONE, RestorePositionF=False):
    if StateIndex not in sm.states: return
    sm.states[StateIndex].single_entry.add(get_SeAccept(AcceptanceId, PreContextId, RestorePositionF))
    accept_str  = "%s" % AcceptanceId
    pre_str     = "%s/" % PreContextId if PreContextId != E_PreContextIDs.NONE else ""
    restore_str = "R" if RestorePositionF else ""
    print "(%i) Accept %s%s%s" % (StateIndex, pre_str, accept_str, restore_str)

def add_SeStoreInputPosition(sm, StateIndex, RegisterId):
    if StateIndex not in sm.states: return
    sm.states[StateIndex].single_entry.add(SeStoreInputPosition(RegisterId))
    print "(%i) Store InputP %s" % (StateIndex, RegisterId)

def get_homogeneous_array(EntryN, AcceptanceScheme):
    return [ 
        RecipeAcceptance(deepcopy(AcceptanceScheme), {}, {}) 
        for i in xrange(EntryN) 
    ]

def get_homogeneous_array_ip_offset(EntryN, IpOffsetScheme):
    return [ 
        RecipeAcceptance([SeAccept(0)], IpOffsetScheme, {})
        for i in xrange(EntryN) 
    ]

def get_inhomogeneous_array(EntryN, AcceptanceScheme):
    def get_entry(i, AcceptanceScheme):
        """Let one entry be different."""
        result = deepcopy(AcceptanceScheme)
        if i == 1:  # i = 1, always happens
            # always only take the last as different
            if result is None: result = [ SeAccept(8888) ]
            else:              result[len(result)-1] = SeAccept(8888)
        return result

    return [ 
        RecipeAcceptance(get_entry(i, AcceptanceScheme), {}, {}) 
        for i in xrange(EntryN) 
    ]

def get_inhomogeneous_array_ip_offset(EntryN, IpOffsetScheme):
    def get_entry(i, IpOffsetDb):
        """Let one entry be different."""
        result = deepcopy(IpOffsetDb)
        if i == 1:  # i = 1, always happens
            # always only take the last as different
            if len(result) == 0: result = { 0L: -1 }
            else:                result[len(result)-1] += 1000
        return result

    return [ 
        RecipeAcceptance([SeAccept(0)], get_entry(i, IpOffsetScheme), {})
        for i in xrange(EntryN) 
    ]

def get_inhomogeneous_array_snapshot_map(EntryN, IpOffsetScheme):
    pass

def get_required_variable_set(RecipeArray):
    result = set()
    for recipe in RecipeArray:
        for register_id in recipe.ip_offset_db:
            result.add((E_R.PositionRegister, register_id))
    result.add(E_R.AcceptanceRegister)
    return result

def get_MouthStateInfoAcceptance(EntryN, AcceptanceScheme, HomogeneousF=True):
    info  = MouthStateInfo(FromStateIndexSet=set(xrange(EntryN)))
    if HomogeneousF:
        array = get_homogeneous_array(EntryN, AcceptanceScheme)
    else:
        array = get_inhomogeneous_array(EntryN, AcceptanceScheme)

    return configure_MoutStateInfo(info, array)

def get_MouthStateInfoIpOffset(EntryN, IpOffsetScheme, HomogeneousF=True):
    info  = MouthStateInfo(FromStateIndexSet=set(xrange(EntryN)))
    if HomogeneousF:
        array = get_homogeneous_array_ip_offset(EntryN, IpOffsetScheme)
    else:
        array = get_inhomogeneous_array_ip_offset(EntryN, IpOffsetScheme)

    return configure_MoutStateInfo(info, array)

def get_MouthStateInfoSnapshotMap(EntryN, AcceptanceScheme, IpOffsetScheme):
    info = MouthStateInfo(FromStateIndexSet=set(xrange(EntryN)))

    acceptance_array = get_homogeneous_array(EntryN, AcceptanceScheme)
    ip_offset_array  = get_homogeneous_array_ip_offset(EntryN, IpOffsetScheme)

    array = [
        RecipeAcceptance(r0.accepter, r1.ip_offset_db, {})
        for r0, r1 in izip(acceptance_array, ip_offset_array)
    ]

    required_variable_set = get_required_variable_set(array)
    snapshot_map = dict(
        (variable_id, state_index)
        for state_index, variable_id in enumerate(sorted(list(required_variable_set)))
    )
    snapshot_map_differing = copy(snapshot_map) 
    for i, variable_id in enumerate(sorted(list(required_variable_set))):
        if i % 2: continue
        # DIFFER for 'variable_id'
        snapshot_map_differing[variable_id] = snapshot_map[variable_id] + 1

    for i, recipe in enumerate(array):
        if i == 1: recipe.snapshot_map = snapshot_map_differing
        else:      recipe.snapshot_map = snapshot_map
        info.entry_recipe_db[i]    = recipe
        info.required_variable_set = required_variable_set

    return configure_MoutStateInfo(info, array)

def configure_MoutStateInfo(info, RecipeArray):
    required_variable_set = get_required_variable_set(RecipeArray)
    for i, recipe in enumerate(RecipeArray):
        info.entry_recipe_db[i]    = recipe
        info.required_variable_set = required_variable_set

    return info

def print_recipe(si, R):
    if R is None: 
        print "  %02i <void>" % si
    else:
        print "  %02i %s" % (si, str(R).replace("\n", "\n     "))

def print_mouth(si, Mouth):
    print_recipe(si, Mouth.recipe)
    print_snapshot_map(Mouth.recipe.snapshot_map)
    print_entry_recipe_db(Mouth.entry_recipe_db)

def print_snapshot_map(SnapshotMap):
    print "  snapshot_map: [%s]" % "".join("%s@%s" % (x,y) for x,y in SnapshotMap.iteritems())

def print_entry_recipe_db(si, EntryRecipeDb):
    print
    print " * %02i\n" % si
    for from_si, recipe in sorted(EntryRecipeDb.iteritems()):
        if recipe is None: 
            print "  from %02s <void>" % from_si
        else:
            print "  from %02s \n     %s" % (from_si, str(recipe).replace("\n", "\n     "))

def unique_set(EntryRecipeDb, access):
    result = []
    for entry_recipe in EntryRecipeDb.itervalues():
        x = access(entry_recipe)
        if x not in result:
            result.append(x)
    return result

def print_acceptance_scheme(info, Prefix=""):
    accepter_set = unique_set(info.entry_recipe_db, lambda x: x.accepter)

    if len(accepter_set) == 0:
        pass
    elif len(accepter_set) == 1:
        print Prefix + "Common Acceptance Scheme:"
        print Prefix + RecipeAcceptance.get_string_accepter(accepter_set.pop()).replace("\n", "\n%s" % Prefix)
    else:
        print "Acceptance Schemes:"
        def key(accepter):
            return (len(accepter), tuple(x.acceptance_id() for x in accepter))

        for accepter in sorted(list(accepter_set), key=key):
            print Prefix + "  --"
            print Prefix + RecipeAcceptance.get_string_accepter(accepter).replace("\n", "\n%s" % Prefix)

def print_ip_offset_scheme(info, Prefix=""):
    print Prefix + "Input Pointer Offset Schemes:"

    all_set = set(flatten_list_of_lists(
        entry_recipe.ip_offset_db.keys()
        for entry_recipe in info.entry_recipe_db.values()
    ))
    if not all_set:
        print
        return 

    L = max(len("%s" % x) for x in all_set)
    predecessor_list = sorted(info.entry_recipe_db.iterkeys())
    print Prefix + "   %s      %s" % (" "*L, "".join("%-10s" % si for si in predecessor_list))

    for position_register in sorted(list(all_set)):
        scheme = [
            info.entry_recipe_db[si].ip_offset_db.get(position_register)
            for si in predecessor_list
        ]
        name        = "%s" % position_register
        space       = " " * (L - len(name))
        print Prefix + "   %s:%s %s" % (name, space, "".join("%8s, " % x if x is not None else "<reload>, " for x in scheme))
    print

def print_snapshot_map_scheme(info, Prefix=""):
    print Prefix + "Snapshot Map Schemes:"

    all_set = set(flatten_list_of_lists(
        entry_recipe.snapshot_map.keys()
        for entry_recipe in info.entry_recipe_db.values()
    ))
    if not all_set:
        print
        return 

    L = max(len("%s" % repr(x)) for x in all_set)
    predecessor_list = sorted(info.entry_recipe_db.iterkeys())
    print Prefix + "   %s      %s" % (" "*L, "".join("%-10s" % si for si in predecessor_list))

    for variable_id in sorted(list(all_set)):
        scheme = [
            info.entry_recipe_db[si].snapshot_map.get(variable_id)
            for si in predecessor_list
        ]
        name  = "%s" % repr(variable_id)
        space = " " * (L - len(name))
        print Prefix + "   %s:%s %s" % (name, space, "".join("%8s, " % x if x is not None else "          " for x in scheme))
    print

def print_interference_result(MouthDb):
    print "Mouth States:"
    for si, info in MouthDb.iteritems():
        print_acceptance_scheme(info, Prefix="##")
        print_ip_offset_scheme(info, Prefix="##")
        print_snapshot_map_scheme(info, Prefix="##")

        print "Output Recipe:"
        print_recipe(si, info.recipe)

        print "--------------------------------------------------------------------"

