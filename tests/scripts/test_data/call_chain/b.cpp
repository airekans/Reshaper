#include "b.h"

void bar(){
	Test_ns::TargetFunc(3);
}

void TargetFunc(int i){
}

void foo(){
	bar();
}
