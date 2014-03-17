
class RegisterAccessDB(dict):
    def __init__(self, RegisterAccessInfoList):
        for info in RegisterAccessInfoList:
            register_id = info[0]
            rights      = info[1]
            if len(info) == 3: 
                sub_id_reference = info[2]
                register_id = (register_id, sub_id_reference)
            self[register_id] = RegisterAccessRight(rights & r, rights & w)

__access_db = None
__content_db = None   
__brancher_set = None 
_cost_db       = None 

