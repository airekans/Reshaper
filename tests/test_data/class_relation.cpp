#include "class_relation.h"


void A::m_func1()
{
	X x;
	x.m_funcx();
	m_other.f();
}

void A::m_func2()
{
	std::auto_ptr<Y> pY(new Y1);
	pY->m_f = 1.8;

	m_func1();
}


void A::m_func3(Z* z)
{
	z->m_funcz();
}
