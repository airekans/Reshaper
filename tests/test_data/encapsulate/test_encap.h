class A{
    int m_i;
public:
    int m_i2;
private:
    int m_i3;
public:
    int m_i4;
};

struct B{
    int m_i;
    int m_i2;
private:
    int m_i3;
};

class C{
	int m_i;
};

class D{
public:
	C m_c;
};

class E{
public:
	int m_i1;
	int m_i2;
	int m_i3;
	int foo();
	int GetI1();
};