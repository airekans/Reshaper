""" classprinter provides ClassPrinter used to "print" out a C++ class
according to the attributes set on it.
"""

from util import get_function_signature


class ClassPrinter(object):
    """ ClassPrinter is used to generate a class in a files
    """
    
    def __init__(self, name):
        """
        
        Arguments:
        - `name`: class name
        """
        self._name = name
        self._methods = []
        self._members = []

    def __get_declaration(self):
        return "class " + self._name

    def __get_default_destructor(self):
        return "virtual ~%s {}" % self._name

    def __get_virtual_method(self, method):
        if method.startswith("virtual"):
            return method
        else:
            return "virtual " + method
            
    def __get_pure_virtual_method(self, method):
        virtual_method = self.__get_virtual_method(method)
        if virtual_method.endswith("0"):
            return virtual_method
        else:
            return virtual_method + " = 0"

    def __get_pure_virtual_signature(self, method):
        return self.__get_pure_virtual_method(get_function_signature(method))

    def set_methods(self, methods):
        self._methods = methods

    def set_members(self, members):
        self._members = members

    def get_forward_declaration(self):
        return self.__get_declaration() + ";"

    def get_definition(self):
        indent = "    "
        method_signatures = [get_function_signature(m) for m in self._methods]
        methods = "\n".join([indent + self.__get_default_destructor()] +
                            [indent + self.__get_pure_virtual_method(m) + ";"
                             for m in method_signatures
                             if not m.startswith(("template", "static"))])
        # TODO: add members

        class_def = """%s
{
public:
%s
};""" % (self.__get_declaration(), methods)
        return class_def
        
