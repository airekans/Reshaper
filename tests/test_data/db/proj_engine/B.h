#ifndef B_H
#define B_H

template<typename T>
class B
{
public:
	B() {}
	~B() {}

	const T& GetData() const { return m_data; }

private:
	T m_data;
};

#endif

