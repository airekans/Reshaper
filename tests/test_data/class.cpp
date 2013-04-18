#include "class.h"


TestStruct A::result_test_fun(TestStruct* t)
{
    if (t != 0)
    {
	return *t;
    }
    else
    {
	return TestStruct();
    }
}



