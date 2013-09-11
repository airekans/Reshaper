#ifndef _NO_SOURCE_HEADER_
#define _NO_SOURCE_HEADER_

#include "indirectly_include.h"

class NoSourceHeader
{
public:
    void SetIndirectly(IndirectlyInclude* in)
    {
        m_indInclude = in;
    }
    IndirectlyInclude* GetIndirectly() const
    {
        return m_indInclude;
    }
private:
    IndirectlyInclude* m_indInclude;
};

#endif // _NO_SOURCE_HEADER_

