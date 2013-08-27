#import "c.h"

void foo(){
	Test t;
	t.TargetFunc1();
}

int TargetFunc2(){
	return 1;
}


namespace {
	void TargetFunc3(){
		TargetFunc2();
	}
}

namespace Test_ns{
	void TargetFunc4(){
	}
}
