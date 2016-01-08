#!/usr/bin/python

import os
import re
import sys
import unittest
import argparse
import xmlrunner

__version__ = '0.0.2'

if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

from distaf.util import testcases, test_list, distaf_init, distaf_finii, \
                        test_seq, test_mounts


def collect_tests(_dir="tests_d"):
    """
        Collects all the tests and populates them in a global list 'ts'
        Each element of the list is the tuple of name of testcase name it's
        function object. The function object is later used to set the tests
        to gluster_tests class.
    """
    if os.path.isfile(_dir):
        __import__((_dir.replace(".py", "")).replace("/", "."))
    else:
        for top, _, files in os.walk(_dir, topdown=False):
            for _f in files:
                if _f.startswith("test_") and  _f.endswith(".py"):
                    iname = top + '/' + _f.replace(".py", "")
                    # When testcase is imported, decorator populates the
                    # Testcase and its value in a tuple. And that will be later
                    # added to ts list
                    __import__(iname.replace("/", "."))


class gluster_tests(unittest.TestCase):
    """
        Empty class. But will be populated with test cases during runtime
    """
    pass


def set_tests(tests=''):
    """
        Sets the gluster_tests Test class with the test cases.
        Name of the tests will be prepended with test_ to enable
        unittest to recognise them as test case
    """
    if tests == '':
        tests = testcases.keys()
    if test_list == {}:
        test_list[''] = testcases.keys()
    i = 0
    for voltype, vol_tests in test_list.iteritems():
        for test in vol_tests:
            if test in tests:
                if test not in test_mounts:
                    test_mounts[test] = ['']
                for mount in test_mounts[test]:
                    try:
                        setattr(gluster_tests, "test_%d_%s_%s_%s" % \
                                (i, voltype, mount, test), testcases[test])
                        i = i + 1
                        test_seq.append((voltype, mount))
                    except KeyError:
                        sys.stderr.write("Unable to find test %s." \
                                         "Skipping...\n" % test)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", help="Test case(s) to run")
    parser.add_argument("-d", help="Directory to choose tests from")
    parser.add_argument("-f", help="Find the test cases from the file")
    parser.add_argument("-c", help="The (yaml) config file to use",
                              default="config.yml")
    parser.add_argument("-j", help="Directory to store JUnit XML file",
                              action="store",
                              dest="xmldir")
    args = parser.parse_args()

    _ = distaf_init(args.c)

    if args.f != None:
        collect_tests(args.f)
        set_tests()
    elif args.d != None and args.t != None:
        collect_tests("tests_d/%s" % args.d)
        set_tests(args.t.split(' '))
    elif args.t != None:
        collect_tests()
        set_tests(args.t.split(' '))
    elif args.d != None:
        collect_tests("tests_d/%s" % args.d)
        set_tests()
    else:
        collect_tests()
        set_tests()

    get_num = lambda x: int(re.search(r'test_([0-9]+)_', x).group(1))
    sortcmp = lambda _, x, y: cmp(get_num(x), get_num(y))
    unittest.TestLoader.sortTestMethodsUsing = sortcmp

    if args.xmldir != None:
        runner = xmlrunner.XMLTestRunner(output=args.xmldir)
    else:
        runner = unittest.TextTestRunner(verbosity=2)

    itersuite = unittest.TestLoader().loadTestsFromTestCase(gluster_tests)
    runner.run(itersuite)
    distaf_finii()

if __name__ == '__main__':
    main()
