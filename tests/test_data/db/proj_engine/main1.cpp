#include "B.h"
#include "A.h"

int main()
{
	B<A> b;
	const A &a = b.GetData();

	return 0;
}
