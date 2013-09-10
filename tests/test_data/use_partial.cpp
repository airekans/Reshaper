#include "static_func.h"
#include "typedef.h"
#include "macro.h"
#include "enum_header.h"

int main()
{
    StaticClass *p_StaticClass = StaticClass::Instance();
    delete p_StaticClass;

    HeaderTwo ht;
    int x = 1;
    int y = 2;

    return Max(x, y);
}

