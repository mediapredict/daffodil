import sys
import os
import json
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from daffodil import Daffodil, PrettyPrintDelegate
from daffodil.exceptions import ParseError


def load_test_data(dataset):
    filename = os.path.join(os.path.dirname(__file__), 'data', '{0}.json'.format(dataset))
    return json.load(open(filename))

def load_nyc_opendata(dataset):
    dataset = load_test_data(dataset)
    columns = [c['fieldName'] for c in dataset['meta']['view']['columns']]
    d = [dict(zip(columns, row_values)) for row_values in dataset['data']]


class SATDataTests(unittest.TestCase):

    def setUp(self):
        self.d = load_test_data('nyc_sat_scores')

    def filter(self, daff_src):
        return Daffodil(daff_src)(self.d)

    def assert_filter_has_n_results(self, n, daff_src):
        self.assertEqual(len(self.filter(daff_src)), n)

    def test_no_filters(self):
        self.assertEqual(len(self.d), 421)

    def test_empty(self):
        self.assert_filter_has_n_results(421, "")
        self.assert_filter_has_n_results(421, "{}")
        self.assert_filter_has_n_results(0, "[]")

    def test_int_eq(self):
        self.assert_filter_has_n_results(4, """
            num_of_sat_test_takers = 50
        """)

    def test_int_ne(self):
        self.assert_filter_has_n_results(417, """
            num_of_sat_test_takers != 50
        """)

    def test_int_gt(self):
        self.assert_filter_has_n_results(273, """
            num_of_sat_test_takers > 50
        """)

    def test_int_gte(self):
        self.assert_filter_has_n_results(277, """
            num_of_sat_test_takers >= 50
        """)

    def test_int_lt(self):
        self.assert_filter_has_n_results(144, """
            num_of_sat_test_takers < 50
        """)

    def test_int_lte(self):
        self.assert_filter_has_n_results(148, """
            num_of_sat_test_takers <= 50
        """)

    def test_float_eq(self):
        self.assert_filter_has_n_results(0, """
            num_of_sat_test_takers = 50.5
        """)

    def test_float_ne(self):
        self.assert_filter_has_n_results(421, """
            num_of_sat_test_takers != 50.5
        """)

    def test_float_gt(self):
        self.assert_filter_has_n_results(273, """
            num_of_sat_test_takers > 50.5
        """)

    def test_float_gte(self):
        self.assert_filter_has_n_results(277, """
            num_of_sat_test_takers >= 50.0
        """)

    def test_float_lt(self):
        self.assert_filter_has_n_results(144, """
            num_of_sat_test_takers < 49.5
        """)

    def test_float_lte(self):
        self.assert_filter_has_n_results(148, """
            num_of_sat_test_takers <= 50.0
        """)

    def test_multiple(self):
        self.assert_filter_has_n_results(3, """
            num_of_sat_test_takers = 10
            sat_writing_avg_score < 400
            sat_math_avg_score > 200
            sat_critical_reading_avg_score <= 500
        """)

    def test_multiple_for_same_value(self):
        self.assert_filter_has_n_results(51, """
            sat_writing_avg_score >= 300
            sat_writing_avg_score < 350
        """)

    def test_or(self):
        self.assert_filter_has_n_results(8, """
            [
                num_of_sat_test_takers = 10
                num_of_sat_test_takers = 11
                num_of_sat_test_takers = 12
            ]
        """)

    def test_and_nested_within_or(self):
        self.assert_filter_has_n_results(134, """
            [
                {
                sat_writing_avg_score >= 300
                sat_writing_avg_score < 350
                }
                {
                sat_writing_avg_score >= 400
                sat_writing_avg_score < 450
                }
            ]
        """)

    def test_or_mixed_with_literal(self):
        self.assert_filter_has_n_results(11, """
            sat_writing_avg_score < 450
            [
                num_of_sat_test_takers = 10
                num_of_sat_test_takers = 11
                num_of_sat_test_takers = 12
                num_of_sat_test_takers = 13
                num_of_sat_test_takers = 14
                num_of_sat_test_takers = 15
            ]
        """)

    def test_and_mixed_with_or(self):
        self.assert_filter_has_n_results(6, """
            {
                sat_writing_avg_score > 350
                sat_writing_avg_score < 500
            }
            [
                num_of_sat_test_takers = 10
                num_of_sat_test_takers = 11
                num_of_sat_test_takers = 12
            ]
        """)

    def test_single_quoted_fields(self):
        self.assert_filter_has_n_results(417, """
            'num_of_sat_test_takers' != 50
        """)
        self.assert_filter_has_n_results(417, """
            'num_of_sat_test_takers' != '50'
        """)

    def test_double_quoted_fields(self):
        self.assert_filter_has_n_results(417, """
            "num_of_sat_test_takers" != 50
        """)
        self.assert_filter_has_n_results(417, """
            "num_of_sat_test_takers" != "50"
        """)

    def test_string_eq(self):
        self.assert_filter_has_n_results(1, """
            school_name = "EAST SIDE COMMUNITY SCHOOL"
        """)
        self.assert_filter_has_n_results(1, """
            school_name = 'EAST SIDE COMMUNITY SCHOOL'
        """)

    def test_string_ne(self):
        self.assert_filter_has_n_results(420, """
            school_name != "EAST SIDE COMMUNITY SCHOOL"
        """)
        self.assert_filter_has_n_results(420, """
            school_name != 'EAST SIDE COMMUNITY SCHOOL'
        """)

    #def test_comparing_a_string_containing_int(self):
    #    self.assert_filter_has_n_results(417, """
    #        num_of_sat_test_takers != "50"
    #    """)

    #def test_comparing_a_string_containing_float(self):
    #    self.assert_filter_has_n_results(417, """
    #        num_of_sat_test_takers != "50.0"
    #    """)

    def test_missing_field(self):
        self.assert_filter_has_n_results(0, """
            numOfSatTestTakers-9-17-2013 = 99
        """)
        self.assert_filter_has_n_results(421, """
            numOfSatTestTakers_9-17-2013 != 99
        """)
        self.assert_filter_has_n_results(0, """
            "number of SAT Test Takers 9-17-2013" = 99
        """)
        self.assert_filter_has_n_results(421, """
            "number of SAT Test Takers 9-17-2013" != 99
        """)

    def test_invalid_filter(self):
        self.assertRaises(ParseError, Daffodil, """
            [
        """)

    def test_unicode_filter(self):
        self.assert_filter_has_n_results(273, u"""
            num_of_sat_test_takers > 50
        """)

    def test_existance_has_value(self):
        self.assert_filter_has_n_results(421, u"""
            num_of_sat_test_takers ?= true
        """)
        self.assert_filter_has_n_results(0, u"""
            num_of_sat_test_takers ?= false
        """)
        self.assert_filter_has_n_results(421, u"""
            "num_of_sat_test_takers" ?= true
        """)
        self.assert_filter_has_n_results(0, u"""
            "num_of_sat_test_takers" ?= false
        """)
        self.assert_filter_has_n_results(421, u"""
            'num_of_sat_test_takers' ?= true
        """)
        self.assert_filter_has_n_results(0, u"""
            'num_of_sat_test_takers' ?= false
        """)

    def test_existance_does_not_have_value(self):
        self.assert_filter_has_n_results(0, u"""
            asdf ?= true
        """)
        self.assert_filter_has_n_results(421, u"""
            asdf ?= false
        """)
        self.assert_filter_has_n_results(0, u"""
            "asdf" ?= true
        """)
        self.assert_filter_has_n_results(421, u"""
            "asdf" ?= false
        """)
        self.assert_filter_has_n_results(0, u"""
            'asdf' ?= true
        """)
        self.assert_filter_has_n_results(421, u"""
            'asdf' ?= false
        """)
    
    def test_comparing_string_data_to_an_int_filter(self):
        self.assert_filter_has_n_results(0, """
            dbn = 7
        """)
        self.assert_filter_has_n_results(0, """
            dbn > 7
        """)
        self.assert_filter_has_n_results(421, """
            dbn != 7
        """)
        self.assert_filter_has_n_results(0, """
            dbn = -7
        """)
        self.assert_filter_has_n_results(0, """
            dbn > -7
        """)
        self.assert_filter_has_n_results(421, """
            dbn != -7
        """)
    
    def test_comparing_string_data_to_a_float_filter(self):
        self.assert_filter_has_n_results(0, """
            dbn = 7.5
        """)
        self.assert_filter_has_n_results(0, """
            dbn > 7.5
        """)
        self.assert_filter_has_n_results(421, """
            dbn != 7.5
        """)
        self.assert_filter_has_n_results(0, """
            dbn = -7.5
        """)
        self.assert_filter_has_n_results(0, """
            dbn > -7.5
        """)
        self.assert_filter_has_n_results(421, """
            dbn != -7.5
        """)


class PredicateTests(unittest.TestCase):
    def setUp(self):
        self.data = {
          "MHQ9ProgsWatched - GoldRush": "no",
          "MHQ9ProgsWatched - PawnStars": "yes",
          "MHQ9ProgsWatched - BornSurvivor": "no",
          "MHQ9ProgsWatched - AirCrashInvestigation": "no",
          "MHQ9ProgsWatched - AmericanPickers": "no",
          "MHQ9ProgsWatched - StorageWars": "yes",
          "MHQ9ProgsWatched - TopGear": "no",
          "MHQ9ProgsWatched - FifthGear": "no",
          "MHQ9ProgsWatched - WheelerDealers": "no",
          "MHQ9ProgsWatched - FastNLoud": "no",
          "MHQ9ProgsWatched - MythBusters": "no",
          "MHQ9ProgsWatched - DeadliestCatch": "no",
          "MHQ9ProgsWatched - WickedTuna": "no",
          "MHQ9ProgsWatched - AuctionHunters": "no",
          "MHQ9ProgsWatched - AmericanChopper": "no",
          "MHQ9ProgsWatched - SonsOfGuns": "no"
        }

    def test_keys(self):
        daff = Daffodil("""
        {
          "k1" = "no"
          [
            k2 = 1.7
            k3 > 5
          ]
          [
            "k4" ?= true
            "k5" = "words"
          ]
        }
        """)
        self.assertEqual(daff.keys, set(["k1", "k2", "k3", "k4", "k5"]))
    
    def test_matching(self):
        daff = Daffodil("""
        {
           "MHQ9ProgsWatched - BornSurvivor" = "no"
           "MHQ9ProgsWatched - WheelerDealers" = "no"
           "MHQ9ProgsWatched - FifthGear" = "no"
           "MHQ9ProgsWatched - AuctionHunters" = "no"
           "MHQ9ProgsWatched - MythBusters" = "no"
           "MHQ9ProgsWatched - GoldRush" = "no"
           "MHQ9ProgsWatched - DeadliestCatch" = "no"
           "MHQ9ProgsWatched - FastNLoud" = "no"
           "MHQ9ProgsWatched - SonsOfGuns" = "no"
           "MHQ9ProgsWatched - AmericanChopper" = "no"
        }
        """)
        self.assertTrue(daff.predicate(self.data))

        daff = Daffodil(u"""{
           "MHQ9ProgsWatched - BornSurvivor" = 'no'
           "MHQ9ProgsWatched - WheelerDealers" = 'no'
           "MHQ9ProgsWatched - FifthGear" = 'no'
           "MHQ9ProgsWatched - AuctionHunters" = 'no'
           "MHQ9ProgsWatched - MythBusters" = 'no'
           "MHQ9ProgsWatched - GoldRush" = 'no'
           "MHQ9ProgsWatched - DeadliestCatch" = 'no'
           "MHQ9ProgsWatched - FastNLoud" = 'no'
           "MHQ9ProgsWatched - SonsOfGuns" = 'no'
           "MHQ9ProgsWatched - AmericanChopper" = 'no'
        }""")
        self.assertTrue(daff.predicate({
           u'MHQ9ProgsWatched - PawnStars': u'yes', u'MHQ3Gender': u'Female', u'MHQ9ProgsWatched - FastNLoud': u'no', u'MHQ8ChannelViewing - Discovery Channel': u'OncePerWeek', u'MHQ8ChannelViewing - National Geographic': u'OncePerWeek', '_sample_id': u'frutest3', u'MHQ4TVProvider - YouView': u'no', u'MHQ6Industry - MarketResearch': u'no', u'MHQ6Industry - Entertainment': u'no', u'MHQ5TVViewing': u'1-3nights', u'MHQ8ChannelViewing - ITV1': u'OncePerWeek', u'MHQ7PastParticipant': u'No', u'MHQ9ProgsWatched - StorageWars': u'yes', u'MHQ8ChannelViewing - History Channel': u'OncePerWeek', u'MHQ8ChannelViewing - BBC2': u'OncePerWeek', u'MHQ1Confidential': u'Yes', u'MHQ4TVProvider - Freeview': u'no', u'MHQ9ProgsWatched - BornSurvivor': u'no', u'MHQ9ProgsWatched - WheelerDealers': u'no', u'MHQ8ChannelViewing - Channel4': u'OncePerWeek', u'MHQ4TVProvider - IPTV': u'no', u'MHQ9ProgsWatched - AuctionHunters': u'no', u'MHQ9ProgsWatched - AirCrashInvestigation': u'no', u'MHQ8ChannelViewing - Sky Arts': u'OncePerWeek', u'MHQ2Age': u'18-34', u'MHQ8ChannelViewing - BBC1': u'OncePerWeek', u'MHQ6Industry - None': u'yes', u'MHQ4TVProvider - None': u'no', u'MHQ6Industry - RadioTV': u'no', u'MHQ6Industry - Advertising': u'no', u'MHQ9ProgsWatched - DeadliestCatch': u'no', u'MHQ9ProgsWatched - FifthGear': u'no', u'MHQ9ProgsWatched - TopGear': u'no', u'MHQ9ProgsWatched - SonsOfGuns': u'no', u'MHQ9ProgsWatched - WickedTuna': u'no', u'MHQ9ProgsWatched - GoldRush': u'no', u'MHQ9ProgsWatched - MythBusters': u'no', u'MHQ6Industry - Press': u'no', u'MHQ4TVProvider - Virgin': u'yes', '_id': '41298', u'MHQ9ProgsWatched - AmericanPickers': u'no', u'MHQ9ProgsWatched - AmericanChopper': u'no', u'MHQ4TVProvider - Sky': u'no'
        }))

    def test_not_matching(self):
        daff = Daffodil("""
        {
           "MHQ9ProgsWatched - MythBusters" = "yes"
           "MHQ9ProgsWatched - BornSurvivor" = "no"
           "MHQ9ProgsWatched - WheelerDealers" = "no"
           "MHQ9ProgsWatched - FifthGear" = "no"
           "MHQ9ProgsWatched - AuctionHunters" = "no"
           "MHQ9ProgsWatched - GoldRush" = "no"
           "MHQ9ProgsWatched - DeadliestCatch" = "no"
           "MHQ9ProgsWatched - FastNLoud" = "no"
           "MHQ9ProgsWatched - SonsOfGuns" = "no"
           "MHQ9ProgsWatched - AmericanChopper" = "no"
        }
        """)

        self.assertFalse(daff.predicate(self.data))



# input, expected_dense, expected_pretty
PRETTY_PRINT_EXPECTATIONS = (

# Simple
[
'''
    val1 = 10
    val2 = 20
''',
'{"val1"=10,"val2"=20}',
'''
{
  "val1" = 10
  "val2" = 20
}
'''.strip()
],

# Simple - out of order
[
'''
    val2 = 20
    val1 = 10
''',
'{"val1"=10,"val2"=20}',
'''
{
  "val1" = 10
  "val2" = 20
}
'''.strip()
],

# Explicit All
[
'''
{
    val1 = 10
    val2 = 20
}
''',
'{"val1"=10,"val2"=20}',
'''
{
  "val1" = 10
  "val2" = 20
}
'''.strip()
],

# Unnecessary nested All
[
'''
{
  {
    val1 = 10
    val2 = 20
  }
}
''',
'{"val1"=10,"val2"=20}',
'''
{
  "val1" = 10
  "val2" = 20
}
'''.strip()
],

# Unnecessary nested All (inside an any)
[
'''
[
  {
    val1 = 10
    val2 = 20
  }
] 
''',
'{"val1"=10,"val2"=20}',
'''
{
  "val1" = 10
  "val2" = 20
}
'''.strip()
],

# Simple Any
[
'''
[
    val1 = 10
    val2 = 20
]
''',
'["val1"=10,"val2"=20]',
'''
[
  "val1" = 10
  "val2" = 20
]
'''.strip()
],



# Unnecessary nested Any
[
'''
[
  [
    val1 = 10
    val2 = 20
  ]
]
''',
'["val1"=10,"val2"=20]',
'''
[
  "val1" = 10
  "val2" = 20
]
'''.strip()
],

# Unnecessary nested Any (inside an all)
[
'''
{
  [
    val1 = 10
    val2 = 20
  ]
}
''',
'["val1"=10,"val2"=20]',
'''
[
  "val1" = 10
  "val2" = 20
]
'''.strip()
],

# simple + nested Any inside an all
[
'''
{
  val1 = 10
  [
    val2 = 20
    val3 = 30
  ]
}
''',
'{"val1"=10,["val2"=20,"val3"=30]}',
'''
{
  "val1" = 10
  [
    "val2" = 20
    "val3" = 30
  ]
}
'''.strip()
],

# simple + nested All inside an Any
[
'''
[
  val1 = 10
  {
    val2 = 20
    val3 = 30
  }
]
''',
'["val1"=10,{"val2"=20,"val3"=30}]',
'''
[
  "val1" = 10
  {
    "val2" = 20
    "val3" = 30
  }
]
'''.strip()
],

[
r'v="a"',
r'{"v"="a"}',
'''
{
  "v" = "a"
}
'''.strip(),
],

# Escaped double quote
[
r'v="\"a"',
r'{"v"="\"a"}',
'''
{
  "v" = "\\"a"
}
'''.strip(),
],

# Escaped single quote
[
r"v='\'a'",
'{"v"="\'a"}',
'''
{
  "v" = "'a"
}
'''.strip(),
],



# Complex, unordered, badly indented and nested
[
'''
val2 = 3  
val2 ?= true
    val1 < 10
  val9 = "what's \\"up\\"?"
[
  {
val6 ?= true
      val5 = 30
    }  
  {
    val5 ?= true
    val5 != 30
  }, val99 < 5.525 ]

''',
'{"val1"<10,"val2"=3,"val2"?=true,"val9"="what\'s \\"up\\"?",["val99"<5.525,{"val5"!=30,"val5"?=true},{"val5"=30,"val6"?=true}]}',
'''
{
  "val1" < 10
  "val2" = 3
  "val2" ?= true
  "val9" = "what's \\"up\\"?"
  [
    "val99" < 5.525
    {
      "val5" != 30
      "val5" ?= true
    }
    {
      "val5" = 30
      "val6" ?= true
    }
  ]
}
'''.strip()
],

)

class PrettyPrintingTests(unittest.TestCase):
    delegate_dense = PrettyPrintDelegate(dense=True)
    delegate_pretty = PrettyPrintDelegate(dense=False)
    
    def pp(self, fltr):
        dense = Daffodil(fltr, delegate=self.delegate_dense)()
        pretty = Daffodil(fltr, delegate=self.delegate_pretty)()
        return dense, pretty
        
    def assertFilterIsCorrect(self, fltr, expected_dense, expected_pretty):
        dense, pretty = self.pp(fltr)
        self.assertEqual(dense, expected_dense)
        self.assertEqual(pretty, expected_pretty)
    
    def test_simple(self):
        for fltr, dense, pretty in PRETTY_PRINT_EXPECTATIONS:
            self.assertFilterIsCorrect(fltr, dense, pretty)
            
    def test_multiple_passthroughs(self):
        for fltr, dense_expected, pretty_expected in PRETTY_PRINT_EXPECTATIONS:
            d1, p1 = self.pp(fltr)
            d1_dense, d1_pretty = self.pp(d1)
            p1_dense, p1_pretty = self.pp(p1)
            
            self.assertEqual(d1_pretty, pretty_expected)
            self.assertEqual(p1_pretty, pretty_expected)
            self.assertEqual(d1_dense, dense_expected)
            self.assertEqual(p1_dense, dense_expected)
            


# Borrowed gratuitously from https://gist.github.com/k4ml/2219751
from os import path as osp

def rel_path(*p):
    return osp.normpath(osp.join(rel_path.path, *p))

rel_path.path = osp.abspath(osp.dirname(__file__))
this = osp.splitext(osp.basename(__file__))[0]

from django.conf import settings
SETTINGS = dict(
    SITE_ID=1,
    DATABASES = {
        'default':{
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'daffodil_hstore_test',
            'USER': "postgres",
        }
    },
    DEBUG=True,
    TEMPLATE_DEBUG=True,
    INSTALLED_APPS=[
        "django_hstore",
        "testapp",
    ],
    ROOT_URLCONF=this,
    MIDDLEWARE_CLASSES=(),
)

if not settings.configured:
    settings.configure(**SETTINGS)

import django
try:
    django.setup()
except AttributeError:
    pass


from daffodil.hstore_predicate import HStoreQueryDelegate
from testapp.models import BasicHStoreData


class SATDataTestsWithHStore(SATDataTests):

    def setUp(self):
        self.d = BasicHStoreData.objects.all()

    def filter(self, daff_src):
        delegate = HStoreQueryDelegate(hstore_field_name="hsdata")
        daff = Daffodil(daff_src, delegate=delegate)
        return daff(self.d)


from django.core import management

if __name__ == "__main__":
    management.call_command("syncdb")

    BasicHStoreData.objects.all().delete()
    for record in load_test_data('nyc_sat_scores'):
        BasicHStoreData.objects.create(hsdata=record)

    unittest.main()

