'''
Created on 2013-3-5

@author: liangzhao
'''
import reshaper.code_generator as cg 
import os

TEST_HEADER_FILE = os.path.join(os.path.dirname(__file__), './test_data/test.h')


import unittest
class Test(unittest.TestCase):
    
    def test_generate_code(self):
        expected_code = u'''\
template<class Archive>
void serialize(Archive & ar, const unsigned int version)
{
    ar & m_d;
    ar & m_i1;
    ar & m_i2;
    ar & m_i3;
    ar & m_i4;
    ar & m_s1;
    ar & m_x;
    //todo: the following pointer type members are not serialized
    // m_p1;
    // m_p2;
    // m_p3; 
}\
'''
        code = cg.generate_serialize_code(TEST_HEADER_FILE, 'A')
        self.assertEqual(expected_code,
                         code)
        expected_code = u'''\
friend bool operator == (const A & a, const A  & b)
{ 
          return (    
                  a.m_d == b.m_d &&    
                  a.m_i1 == b.m_i1 &&    
                  a.m_i2 == b.m_i2 &&    
                  a.m_i3 == b.m_i3 &&    
                  a.m_i4 == b.m_i4 &&    
                  a.m_s1 == b.m_s1 &&    
                  a.m_x == b.m_x &&    
                  *(a.m_p1) == *(b.m_p1) &&    
                  *(a.m_p2) == *(b.m_p2) &&    
                  *(a.m_p3) == *(b.m_p3) &&
                  true);
}\
'''        
        code = cg.generate_eq_op_code(TEST_HEADER_FILE, \
                                      'A')                         
        self.assertEqual( expected_code, code)
        
        
if __name__ == "__main__":
    unittest.main()
