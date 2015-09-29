from distaf.client_rpyc import big_bang
testcases = {}
tc = big_bang()


def inject_gluster_logs(label, servers=''):
    """
        Injects the label in gluster related logs

        This is mainly to help identifying what was going
        on during the test case

        @parameter: A label string which will be injected to gluster logs
                    A list of servers in which this log inejection should be
                    done

        @returns: None
    """
    if servers == '':
        servers = tc.all_nodes
    cmd = "for file in `find $(gluster --print-logdir) -type f " \
            "-name '*.log'`; do echo \"%s\" >> $file; done" % label
    tc.run_servers(cmd, servers=servers, verbose=False)
    return None


def testcase(name):
    def decorator(func):
        def wrapper(self):
            tc.logger.info("Starting the test: %s" % name)
            inject_gluster_logs(name)
            ret = func()
            self.assertTrue(ret, "Testcase %s failed" % name)
            inject_gluster_logs(name)
            tc.logger.info("Ending the test: %s" % name)
            return ret
        testcases[name] = wrapper
        return wrapper
    return decorator


def finii():
    tc.fini()
