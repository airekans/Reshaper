#ifndef _STATIC_FUNC_H
#define _STATIC_FUNC_H

class StaticClass
{
public:
    static StaticClass* Instance()
    {
        return new StaticClass();
    }
private:
    StaticClass()
    {
    }
};

#endif

