typedef int* PINT;

class A
{
public:
	int m_i;
	PINT m_pint;
	int* m_pi;
	float m_f;
	char m_c;
	bool m_b;
	int m_fpu();
private:
	int m_pri;
	int m_fpi();
public:
	int m_i3 = 3;
private:
	int m_i4;
};

class B
{
public:
	int m_i;
};
