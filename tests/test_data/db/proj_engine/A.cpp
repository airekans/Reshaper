#include "A.h"

A::A()
: m_data(0)
{

}

A::~A()
{}

int A::GetData() const
{
	return m_data;
}

void A::SetData(const int data)
{
	m_data = data;
}
