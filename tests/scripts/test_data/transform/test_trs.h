typedef int* PINT;

template <class numtype>
class shareptr
{
public:
	shareptr operator=(const shareptr ptr){
		return *this;
	}
};

class A
{
public:
	int m_i;
	PINT m_pint;
	int* m_pi;
	float m_f;
	char m_c;
	bool m_b;
	bool GetB();
	int foo();
private:
	int m_pri;
	int bar();
public:
	int m_i3 = 3;
};

struct C
{
};

class B
{
public:
	int m_i;
	A m_a;
	struct C m_c;
	shareptr<int> m_sp1;
	shareptr<int> m_sp2;
};

class D
{
	int foo();
};

int D::foo()
{
	int i = 1;
	i+=1;
	return 1;
}
