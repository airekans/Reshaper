#ifndef _INDIRECTLY_INCLUDE_
#define _INDIRECTLY_INCLUDE_

class IndirectlyInclude
{
public:
    explicit IndirectlyInclude(int i) : m_int(i)
    {
    }
    int GetInt() const
    {
        return m_int;
    }
protected:
private:
    int m_int;
};

#endif // _INDIRECTLY_INCLUDE_

