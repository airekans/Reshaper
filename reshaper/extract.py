""" extract module provides functions and classes to extract class or function 
"""


from util import get_cursors_if
from classprinter import ClassPrinter
from clang.cindex import CursorKind


def extract_interface(class_cursor, methods = None, prefix = "I"):
    """ extract interface from an given class.
    Returns a ClassPrinter representing the interface.
    The default interface name is "I" followed by the class name.
    e.g. class name is "Base", then the interface name is IBase.
    
    Arguments:
    - `class_cursor`: cursor of the class to be extracted
    - `methods`: methods user wants to extract to the interface
    - `prefix`: the interface name prefix used to prepend to the class name
    """

    member_method_cursors = \
        get_cursors_if(class_cursor,
                       lambda c: (c.kind == CursorKind.CXX_METHOD and
                                  (c.spelling in methods
                                   if methods is not None else True)))
    
    # print out the interface class
    class_printer = ClassPrinter(prefix + class_cursor.spelling)
    class_printer.set_methods(member_method_cursors)
    return class_printer
    
