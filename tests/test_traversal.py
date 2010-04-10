from nose.tools import *

from multivisor.models import *
import mock

class TraversalTest(object):

    def setUp(self):
        pass

@raises(KeyError)
def test_tree_node():
    tn = TreeNode()
    tn.router['a_key'] = 'something'
    eq_(tn['a_key'], 'something')
    tn['test']
