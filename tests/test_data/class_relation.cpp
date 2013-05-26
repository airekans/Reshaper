#include "class_relation.h"


void A::m_func1()
{
	X x;
	x.m_func();
}

void A::m_func2()
{
	std::auto_ptr<Y> pY(new Y);
	pY->m_f = 1.8;
}


void A::m_func2(Z* z)
{
	z->m_func();
}
