#include "../test_data1/header_in_other_folder.h"

struct X{
	void m_funcx();
	int m_i;
};

struct Y{
	virtual ~Y(){};
	void m_funcy();
	double m_f;
};

struct Y1: public Y{
};

class XY: public X, private Y
{

};

class Z{
public:
	void m_funcz();
};

class W
{

};

namespace boost{
    template<class X>
    class shared_ptr
    {

    };
};

namespace BT=boost;





using std::auto_ptr;

typedef X XX;
typedef XX* X_PTR;
typedef Y YY;
typedef BT::shared_ptr<YY> YY_PTR;
typedef int INT;
typedef char* CHAR_PRT;

class A0{

};

class A: public A0
{
    X m_x;
    X_PTR m_x1;
    std::auto_ptr<XX> m_x2;
    Y* m_y1;
    YY_PTR m_y2;
    int m_i;
    INT* m_pi;
    CHAR_PRT m_pc;
    Other m_other;

    void m_func1();
    void m_func2();
    void m_func3(Z* z);
};
