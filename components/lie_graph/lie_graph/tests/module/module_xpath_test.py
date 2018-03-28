# -*- coding: utf-8 -*-

"""
file: module_xpath_test.py

Unit tests for XPath query language support in GraphAxis graphs
{2:
  {3:
    {4: 608,
     5: 609,
     6: 610,
     7: 611,
     8: 612,
     9: 613
    },
   10:
    {11: 614,
     12: 615,
     13: 616,
     14: 617,
     15: 618,
     16: 619,
     17: 620,
     18: 621,
     19: 622
     }
   },
  20:
   {
    21:
     {22: 623,
      23: 624,
      24: 625,
      25: 626,
      26: 627,
      27: 628
     },
    28:
     {29: 629,
      30: 630,
      31: 631,
      32: 632,
      33: 633,
      34: 634,
      35: 635,
      36: 636,
      37: 637
      }
    }
  }
"""

import unittest2

from lie_graph import GraphAxis
from lie_graph.graph_query.query_xpath import XpathExpressionEvaluator


class TestXPathQuery(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Create a graph to query
        """

        ala = {'r': 'ALA', 'a':['N', 'CA', 'C', 'O', 'CB', 'H']}
        leu = {'r': 'LEU', 'a':['N', 'CA', 'C', 'O', 'CB', 'CG', 'CD1', 'CD2', 'H']}

        cls.graph = GraphAxis()
        rid = cls.graph.add_node('system')
        cls.graph.root = rid
        start = 1
        atom = 608
        for segid in ('A', 'B'):
            sid = cls.graph.add_node('segid', value=segid)
            cls.graph.add_edge(rid, sid)

            for i, res in enumerate([ala, leu], start=start):

                if start == 1:
                    nid = cls.graph.add_node('residue', value=i, name=res['r'])
                else:
                    nid = cls.graph.add_node('residue', value=i, name=res['r'], extra=True)
                cls.graph.add_edge(sid, nid)

                for atm in res['a']:
                    aid = cls.graph.add_node('atom', value=atom, name=atm, elem=atm[0])
                    cls.graph.add_edge(nid, aid)
                    atom += 1

            start += 1

    def test_query_selfdesc(self):
        """
        Test basic path based query starting from current element (.)
        """

        xpath = XpathExpressionEvaluator()

        # By default we are at root
        self.assertItemsEqual(xpath.resolve('system', self.graph).nodes.keys(), [1])
        self.assertItemsEqual(xpath.resolve('system/segid/residue', self.graph).nodes.keys(), [3, 10, 21, 28])

        # Start search from other node
        sel = self.graph.getnodes(20)
        self.assertItemsEqual(xpath.resolve('system/segid/residue', sel).nodes.keys(), [])
        self.assertItemsEqual(xpath.resolve('segid/residue', sel).nodes.keys(), [21, 28])

    def test_query_rootdesc(self):
        """
        Test root down search using /
        """

        xpath = XpathExpressionEvaluator()

        self.assertItemsEqual(xpath.resolve('/', self.graph).nodes.keys(), [])
        self.assertItemsEqual(xpath.resolve('/system', self.graph).nodes.keys(), [1])
        self.assertItemsEqual(xpath.resolve('/system/segid', self.graph).nodes.keys(), [2, 20])
        self.assertItemsEqual(xpath.resolve('/system/segid/residue', self.graph).nodes.keys(), [3, 10, 21, 28])
        self.assertItemsEqual(xpath.resolve('/system//residue', self.graph).nodes.keys(), [3, 10, 21, 28])
        self.assertItemsEqual(xpath.resolve('/system/segid/residue/atom', self.graph).nodes.keys(), [4, 5, 6, 7, 8, 9,
                    11, 12, 13, 14, 15, 16, 17, 18, 19, 22, 23, 24, 25, 26, 27, 29, 30, 31, 32, 33, 34, 35, 36, 37])

    def test_query_none_rootdesc(self):
        """
        Test root down search using / from non-root position
        """

        xpath = XpathExpressionEvaluator()

        self.assertItemsEqual(xpath.resolve('/segid', self.graph).nodes.keys(), [])
        self.assertItemsEqual(xpath.resolve('/residue', self.graph).nodes.keys(), [])
        self.assertItemsEqual(xpath.resolve('/segid/residue', self.graph).nodes.keys(), [])

    def test_query_descendants(self):
        """
        Test descendant search using //
        """

        xpath = XpathExpressionEvaluator()

        self.assertItemsEqual(xpath.resolve('//', self.graph).nodes.keys(), [])
        self.assertItemsEqual(xpath.resolve('//system', self.graph).nodes.keys(), [1])
        self.assertItemsEqual(xpath.resolve('//segid', self.graph).nodes.keys(), [2, 20])
        self.assertItemsEqual(xpath.resolve('//residue', self.graph).nodes.keys(), [3, 10, 21, 28])
        self.assertItemsEqual(xpath.resolve('//atom', self.graph).nodes.keys(), [4, 5, 6, 7, 8, 9, 11, 12, 13, 14,
                           15, 16, 17, 18, 19, 22, 23, 24, 25, 26, 27, 29, 30, 31, 32, 33, 34, 35, 36, 37])

    def test_query_wildcards(self):
        """
        Test the use of wildcards in the search
        """

        xpath = XpathExpressionEvaluator()

        self.assertItemsEqual(xpath.resolve('//*', self.graph).nodes.keys(), self.graph.nodes.keys())
        self.assertItemsEqual(xpath.resolve('/system/*/residue', self.graph).nodes.keys(), [3, 10, 21, 28])

    def test_query_indexselect(self):
        """
        Test selection of nodes based on index
        """

        xpath = XpathExpressionEvaluator()

        self.assertItemsEqual(xpath.resolve('//*[10]', self.graph).nodes.keys(), [11])
        self.assertItemsEqual(xpath.resolve('//residue[3]', self.graph).nodes.keys(), [28])
        self.assertItemsEqual(xpath.resolve('//residue[4]', self.graph).nodes.keys(), []) # Index out of range
        self.assertItemsEqual(xpath.resolve('//residue[3]/atom', self.graph).nodes.keys(), [29, 30, 31, 32, 33, 34,
                                                                                            35, 36, 37])

    def test_query_attribute_filter(self):
        """
        Test selection of nodes with filter on attributes
        """

        xpath = XpathExpressionEvaluator()

        self.assertItemsEqual(xpath.resolve('//segid[@value]', self.graph).nodes.keys(), [2, 20])
        self.assertItemsEqual(xpath.resolve('//residue[@extra]', self.graph).nodes.keys(), [21, 28])
        self.assertItemsEqual(xpath.resolve('/system/segid/residue/atom[@elem="H"]', self.graph).nodes.keys(),
                              [9, 19, 27, 37])
        self.assertItemsEqual(xpath.resolve('//segid[@value="A"]/residue[@value=1]', self.graph).nodes.keys(), [3])
        self.assertItemsEqual(xpath.resolve('//atom[@value>620]', self.graph).nodes.keys(), [18, 19, 22, 23, 24, 25,
                               26, 27, 29, 30, 31, 32, 33, 34, 35, 36, 37])
        self.assertItemsEqual(xpath.resolve('//atom[@value>620][3]', self.graph).nodes.keys(), [23])
        self.assertItemsEqual(xpath.resolve('//atom[@value<608]', self.graph).nodes.keys(), [])
        #self.assertItemsEqual(xpath.resolve('//atom[@value<=608]', self.graph).nodes.keys(), [4])

        sel = self.graph.getnodes(10)
        self.assertItemsEqual(xpath.resolve('//*[@*]', sel).nodes.keys(), [10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
        self.assertItemsEqual(xpath.resolve('//atom[@*]', sel).nodes.keys(), [11, 12, 13, 14, 15, 16, 17, 18, 19])

    def test_query_different_sepchar(self):
        """
        Test XpathExpressionEvaluator use with different sep char (.)
        """

        xpath = XpathExpressionEvaluator(sep='.')

        xpath.resolve('system.segid.residue', self.graph)