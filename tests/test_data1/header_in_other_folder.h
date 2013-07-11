
namespace std{
    template<class X>
    class auto_ptr
    {
    public:
    	auto_ptr(const X*);
    };
};


class Other
{
public:
	void f();
};
