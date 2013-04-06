
def enum(**enums):
    return type('Enum', (), enums)

AccesssAttr = enum(PUBLIC=1, PROTECTED=2, PRIVATE=3)

class MemberVar(object):
    def __init__(self):
        self.type = ''
        self.is_pointer = False
        self.is_static = False
        self.name = ''
        self.attribute = AccesssAttr.PUBLIC


class ClassInfo(object):
    def __init__(self):
        self.member_vars = []
        self.member_functions = []
        