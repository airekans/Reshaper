'''test serialize_class.py script'''
from tests.util import assert_stdout
import serialize_class
import os

_EXP_OUT = '''\
friend bool operator == (const A& a, const A& b)
{ 
          return (    
                  a.m_i == b.m_i &&    
                  a.m_i2 == b.m_i2 &&    
                  a.m_b == b.m_b &&    
                  *(a.p_int1) == *(b.p_int1) &&    
                  *(a.p_int2) == *(b.p_int2) &&    
                  *(a.p_B) == *(b.p_B) &&
                  true);
}

///serialization function for class A:
template<class Archive>
void serialize(Archive & ar, const unsigned int version)
{
    ar & BOOST_SERIALIZATION_NVP(m_i);
    ar & BOOST_SERIALIZATION_NVP(m_i2);
    ar & BOOST_SERIALIZATION_NVP(p_int1);
    ar & BOOST_SERIALIZATION_NVP(p_int2);
    ar & BOOST_SERIALIZATION_NVP(m_b);
    ar & BOOST_SERIALIZATION_NVP(p_B);       
}'''
@assert_stdout(_EXP_OUT)
def test_serialize_class():
    '''test serialize_class.py script
    '''
    input_file = os.path.join(os.path.dirname(__file__), 
                             'test_data', 'test_serializer.cpp')
    args = [input_file, 'A']
    serialize_class._main(args)