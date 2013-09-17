#include "test_encap.h"

int A::foo(){
	return m_i;
}

int main()
{
	int i;
	A a;
	A* aa = new A();
	a.m_i3 = 10;
	a.m_pint = &i;
	a.m_i = a.m_c + *a.m_pint;
	a.m_b = false;
	a.m_f = float(a.m_i3);

	B b;
	C* pc;
	b.m_a = a;
	b.m_c = pc;
	b.m_sp1 = b.m_sp2;
	return 0;
}
