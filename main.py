#!/usr/bin/python

import os
import re
import sys
import unittest
import argparse
from libs.util import testcases, finii

if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())


def collect_all_tests(dir="tests_d"):
    """
        Collects all the tests and populates them in a global list 'ts'
        Each element of the list is the tuple of name of testcase name it's
        function object. The function object is later used to set the tests
        to gluster_tests class.
    """
    for top, dirs, files in os.walk(dir, topdown=False):
        for f in files:
            if f.startswith("test_") and  f.endswith(".py"):
                iname = top + '/' + f.replace(".py", "")
                # When testcase is imported, decorator populates the
                # Testcase and it's value in a tuple. And that will be later
                # added to ts list
                m = __import__(iname.replace("/", "."))


class gluster_tests(unittest.TestCase):
    """
        Empty class. But will be populated with test cases during runtime
    """
    pass


def set_tests(tests=[]):
    """
        Sets the gluster_tests Test class with the test cases.
        Name of the tests will be prepended with test_ to enable
        unittest to recognise them as test case
    """
    if tests != []:
        i = 0
        for test in tests:
            for name, t in testcases:
                if name == test:
                    # Add the tests to gluster_tests Test Class
                    setattr(gluster_tests, "test_%d_%s" % (i, name), t)
                    i = i + 1
    else:
        i = 0
        for name, t in testcases:
            # Add tests to gluster_tests Test Class
            setattr(gluster_tests, "test_%d_%s" % (i, name), t)
            i = i + 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", help="Test case(s) to run")
    parser.add_argument("-d", help="Directory to choose tests from")
    args = parser.parse_args()
    if args.t != None:
        collect_all_tests()
        set_tests(args.t.split(' '))
    elif args.d != None:
        collect_all_tests("tests_d/%s" % args.d)
        set_tests()
    else:
        collect_all_tests()
        set_tests()
    get_num = lambda x: int(re.search(r'test_([0-9]+)_', x).group(1))
    sortcmp = lambda _, x, y: cmp(get_num(x), get_num(y))
    unittest.TestLoader.sortTestMethodsUsing = sortcmp
    runner = unittest.TextTestRunner(verbosity=2)
    itersuite = unittest.TestLoader().loadTestsFromTestCase(gluster_tests)
    runner.run(itersuite)
    finii()
