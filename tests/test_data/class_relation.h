
struct X{
};

class Y{
};

namespace boost{
    template<class X>
    class shared_ptr
    {

    };
};

namespace BT=boost;


namespace std{
    template<class X>
    class auto_ptr
    {

    };
};


using std::auto_ptr;

typedef X XX;
typedef XX* X_PTR;
typedef Y YY;
typedef BT::shared_ptr<YY> YY_PTR;
typedef int INT;
typedef char* CHAR_PRT;

class A{
    X m_x;
    X_PTR m_x1;
    std::auto_ptr<XX> m_x2;
    Y* m_y1;
    YY_PTR m_y2;
    int m_i;
    INT* m_pi;
    CHAR_PRT m_pc;
};