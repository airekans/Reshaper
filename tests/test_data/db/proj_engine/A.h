#ifndef A_H
#define A_H


class A
{
public:
	A();
	virtual ~A();

	int GetData() const;
	void SetData(const int data);

private:
	int m_data;
};

#endif


