//#include <memory>
//#include <boost/smart_ptr.hpp>
struct X{

};

namespace boost{
	template<class X>
	class shared_ptr
	{

	};
};

namespace std{
	template<class X>
	class auto_ptr
	{

	};
};


using std::auto_ptr;

class A{
	int m_i1;
	int m_i2;
	int m_i3;
	void func1();
protected:
	int m_i4;
    double m_d;
	X* m_p1;
	void func2();
public:
	std::string m_s1;
	boost::shared_ptr<X> m_p2;
	auto_ptr<X> m_p3;
	X m_x;
    void func3();
    static int m_si;
};

typedef A AA;

class B{
	AA m_a;
	X m_x;
};


class B1: public B{
	A* m_pa;
};

class C
{
	void fun();
};

