#include "a.h"

void fooo(){
	foo();
}

void callint(){
	Test t;
	t.TargetFunc(int(3));
}

void callfloat(){
	Test t;
	t.TargetFunc(float(3.5));
}
