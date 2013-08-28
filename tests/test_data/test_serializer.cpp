class B{
};

typedef B* B_Ptr; 
typedef int* p_i;
typedef p_i p_int;
typedef int INT;

class A{
	int m_i;
	INT m_i2;
	static int i;
	p_i p_int1;
	p_int p_int2;
	B m_b;
	B_Ptr p_B;	

	void m_func();
};
