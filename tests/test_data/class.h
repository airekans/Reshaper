// -*- mode: c++ -*-
#ifndef _CLASS_H_
#define _CLASS_H_


struct TestStruct  
{
    int data;
};

class A
{
public:
    A();
    virtual ~A();

    void foo();
    int bar(double d);
    double fun_definition(float f, char* c)
    {
        return 1.0;
    }

    TestStruct result_test_fun(TestStruct*);
    double (*return_fun_fun(int, double))(int, double);
    double fun_with_default_args(const int i = 10);
    virtual void virutal_fun(const double d);
    virtual void pure_virtual_fun(const int i) = 0;
    static void static_fun(int i);
    static bool static_multiline_fun(
         const int i,
         const double d);

    template <typename T>
    void template_fun(const T& t)
    {
	
    }

    int m_i;
};


#endif /* _CLASS_H_ */
