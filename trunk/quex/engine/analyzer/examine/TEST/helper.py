from quex.engine.analyzer.examine.state_info                    import *
from quex.engine.operations.se_operations    import SeAccept, SeStoreInputPosition
from quex.engine.analyzer.examine.acceptance import RecipeAcceptance
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

def print_entry_recipe_db(EntryRecipeDb):
    for predecessor_si, entry_recipe in EntryRecipeDb.iteritems():
        print "  from %i:" % predecessor_si
        print entry_recipe

def unique_set(EntryRecipeDb, access):
    result = []
    for entry_recipe in EntryRecipeDb.itervalues():
        x = access(entry_recipe)
        if x not in result:
            result.append(x)
    return result

def print_acceptance_scheme(info):
    accepter_set = unique_set(info.entry_recipe_db, lambda x: x.accepter)

    if len(accepter_set) == 0:
        pass
    elif len(accepter_set) == 1:
        print "Common Acceptance Scheme:"
        print RecipeAcceptance.get_string_accepter(accepter_set.pop())
    else:
        print "Acceptance Schemes:"
        def key(accepter):
            return (len(accepter), tuple(x.acceptance_id() for x in accepter))

        for accepter in sorted(list(accepter_set), key=key):
            print "  --"
            print RecipeAcceptance.get_string_accepter(accepter)

def print_ip_offset_scheme(info):
    def print_it(ip_offset_db):
        for register, offset in sorted(ip_offset_db.iteritems()):
            print "    [%s]: %s\n" % (register[0], offset)
            
    ip_offset_db_set = unique_set(info.entry_recipe_db,
                                  lambda x: x.ip_offset_db)

    if len(ip_offset_db_set) == 0:
        pass
    elif len(ip_offset_db_set) == 1:
        print "Common Input Pointer Offset Scheme:"
        print RecipeAcceptance.get_string_input_offset_db(ip_offset_db_set.pop())
    else:
        print "Input Pointer Offset Schemes:"
        def key(ip_offset_db):
            return tuple(x for x in ip_offset_db)

        for ip_offset_db in sorted(list(ip_offset_db_set), key=key):
            print "  --"
            print RecipeAcceptance.get_string_input_offset_db(ip_offset_db)

def print_snapshot_map_scheme(info):
    snapshot_map_set = unique_set(info.entry_recipe_db, lambda x: x.snapshot_map)

    if len(snapshot_map_set) == 0:
        pass
    elif len(snapshot_map_set) == 1:
        pass
    else:
        print "SnapshotMap Schemes:"
        def key(snapshot_map):
            return tuple((x,y) for x, y in snapshot_map.iteritems())

        for snapshot_map in sorted(list(snapshot_map_set), key=key):
            print "  --"
            print RecipeAcceptance.get_string_snapshot_map(snapshot_map)

def print_interference_result(MouthDb):
    print "Mouth States:"
    for si, info in MouthDb.iteritems():
        print_acceptance_scheme(info)
        print_ip_offset_scheme(info)
        print_snapshot_map_scheme(info)

        print "Output Recipe:"
        print_recipe(si, info.recipe)

        print "--------------------------------------------------------------------"

