#include "test_ast_dump.h"

int A::foo(){
	return 2;
}

int main(){
	A a;
	int i = a.foo();
	return i;
}
