class A{
	int m_i1;
	int m_i2;
	int m_i3;
	int m_i4;
	int m_i5;
	int m_i6;
    double m_d;
	char* m_s;
};


class B{
	A m_a;
};


class B1: public B{
	A* m_pa;
};
