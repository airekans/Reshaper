#ifndef _B_H_
#define _B_H_

class A;

class B
{
public:
    B(A* a);
    virtual ~B();

    void fun_use_A();
    void fun_not_use_A();

private:
    A* m_a;
};

#endif /* _B_H_ */
