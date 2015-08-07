from distaf.client_rpyc import big_bang
testcases = {}
tc = big_bang()


def testcase(name):
    def decorator(func):
        def wrapper(self):
            ret = func()
            self.assertTrue(ret, "Testcase %s failed" % name)
            return ret
        testcases[name] = wrapper
        return wrapper
    return decorator


def finii():
    tc.fini()
