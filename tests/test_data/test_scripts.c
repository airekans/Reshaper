class D
{
    D();
    virtual ~D();
    void foo();
    int global_d();
};

namespace Outer{
    namespace Inner{
    	class B;
        class C
        {
            C();
            virtual ~C();
            void foo();
            int bar(double d);
        };
        class D
        {
            D();
            virtual ~D();
            void foo();
            int outer_inner_d();
        };
    }
    
    class B
    {
        class D
        {
            D();
            virtual ~D();
            void foo();
            int outer_b_d();
        };
        B();
        virtual ~B();
        void foo();
        int bar(double d);
        Inner::C test_C(*Inner::C);
    };
    
    class D
    {
        D();
        virtual ~D();
        void bar();
        int outer_d();
    };
}

using namespace Outer;

class A
{
public:
    A();
    virtual ~A();
    void foo();
    int bar(double d);
    B test_B(*B);
    Inner::C test_C (*Inner::C);
};
