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
};

