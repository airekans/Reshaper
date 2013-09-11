#include "test_trs.h"

int main()
{
	A a;
	B b;
	A* aa = new A();
	b.m_i = aa->m_i;
	a.m_i3 = 10;
	a.m_i =   a.m_i3 + 3;
	a.m_i =   a.m_i3;
	int j = a.m_i3;
	return 0;
}
