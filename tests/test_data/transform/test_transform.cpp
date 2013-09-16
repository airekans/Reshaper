#include "test_transform.h"

int foo(){
	A a, a2;
	B b;
	a.m_i2 = b.m_i2 + 1;
	int i = a.m_i2;
	a2 = a;
	return a.m_i2;
};

void bar(){
	C c;
	D d;
	d.m_c = c;
	c = d.m_c;
}
