#include "B.h"
#include "class.h"

B::B(A* a)
    : m_a(a)
{
    
}

B::~B()
{
    
}

static void static_fun(const int i)
{
    int data = i + 1;
}

void B::fun_use_A()
{
    static_fun(2);
    int data = m_a->bar(2.0);
    A* a;
    int obj_result = a->bar(1.0);
    obj_result = (*a).bar(1.5);
    A& ref_a = *a;
    obj_result = ref_a.bar(1.5);
    int result = data + 1;
}

void B::fun_not_use_A()
{
    int data = 1;
    int result = data + 2;
}


