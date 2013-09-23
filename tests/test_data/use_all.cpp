#include "static_func.h"
#include "macro.h"
#include "enum_header.h"
#include "typedef.h"

int main()
{
    StaticClass *p_StaticClass = StaticClass::Instance();
    delete p_StaticClass;
    const char* str = HEADER_ONE_STRING;
    MyInt x = MouseClick;
    MyInt y = DoubleClick;

    return Max(x, y);
}
