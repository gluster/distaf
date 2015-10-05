from distaf.client_rpyc import big_bang
from distaf.config_parser import get_global_config, get_testcase_config


testcases = {}
test_list = {}
globl_configs = {}
global_mode = None
tc = None


def distaf_init(config_file="config.yml"):
    """
        The distaf init function which calls the  big_bang
    """
    global globl_configs, global_mode, tc
    globl_configs = get_global_config(config_file)
    global_mode = globl_configs['global_mode']
    tc = big_bang(globl_configs)
    return globl_configs


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
        if not global_mode:
            tc_config = get_testcase_config(func.__doc__)

        def wrapper(self):
            tc.logger.info("Starting the test: %s" % name)
            inject_gluster_logs(name)
            ret = func()
            self.assertTrue(ret, "Testcase %s failed" % name)
            inject_gluster_logs(name)
            tc.logger.info("Ending the test: %s" % name)
            return ret

        testcases[name] = wrapper
        if not global_mode and tc_config is not None:
            for voltype in tc_config['runs_on_volumes']:
                if voltype not in test_list:
                    test_list[voltype] = []
                test_list[voltype].append(name)
        return wrapper

    return decorator


def distaf_finii():
    """
        The fini() function which closes all connection to the servers
    """
    tc.fini()
