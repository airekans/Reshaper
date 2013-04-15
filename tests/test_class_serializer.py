'''
Created on 2013-3-5

@author: liangzhao
'''
import reshaper.class_serializer as cs 
import os

TEST_HEADER_FILE = os.path.join(os.path.dirname(__file__), './test_data/test.h')


import unittest
class Test(unittest.TestCase):
    
    def setUp(self):
        self.maxDiff = None
    
    def test_generate_code(self):
        expected_code = u'''\
serialization function for class A:

template<class Archive>
void serialize(Archive & ar, const unsigned int version)
{
    ar & BOOST_SERIALIZATION_NVP(m_i1);
    ar & BOOST_SERIALIZATION_NVP(m_i2);
    ar & BOOST_SERIALIZATION_NVP(m_i3);
    ar & BOOST_SERIALIZATION_NVP(m_i4);
    ar & BOOST_SERIALIZATION_NVP(m_d);
    ar & BOOST_SERIALIZATION_NVP(m_p1);
    ar & BOOST_SERIALIZATION_NVP(m_s1);
    ar & BOOST_SERIALIZATION_NVP(m_p2);
    ar & BOOST_SERIALIZATION_NVP(m_p3);
    ar & BOOST_SERIALIZATION_NVP(m_x);       
}\
'''
        code = cs.generate_serialize_code(TEST_HEADER_FILE, 'A')
        self.assertEqual(expected_code,
                         code)
        expected_code = u'''\
friend bool operator == (const A& a, const A& b)
{ 
          return (    
                  a.m_i1 == b.m_i1 &&    
                  a.m_i2 == b.m_i2 &&    
                  a.m_i3 == b.m_i3 &&    
                  a.m_i4 == b.m_i4 &&    
                  a.m_d == b.m_d &&    
                  a.m_s1 == b.m_s1 &&    
                  a.m_x == b.m_x &&    
                  *(a.m_p1) == *(b.m_p1) &&    
                  *(a.m_p2) == *(b.m_p2) &&    
                  *(a.m_p3) == *(b.m_p3) &&
                  true);
}\
'''        
        code = cs.generate_eq_op_code(TEST_HEADER_FILE, \
                                      'A')                         
        self.assertEqual( expected_code, code)
        
        
if __name__ == "__main__":
    unittest.main()
