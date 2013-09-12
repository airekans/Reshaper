#include "test_trs.h"

int main()
{
	A a;
	B b;
	int i;
	A* aa = new A();
	b.m_i = aa->m_i;
	a.m_pint = &i;
	a.m_i = a.m_c + *a.m_pint;
	a.m_b = false;
	a.m_f = float(a.m_i3);
	return 0;
}
