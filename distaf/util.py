from types import FunctionType
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
            _ret = True
            if isinstance(func, FunctionType):
                _ret = func()
            else:
                func_obj = func()
                ret = func_obj.setup()
                if not ret:
                    tc.logger.error("The setup of %s failed" % name)
                    _ret = False
                if _ret:
                    ret = func_obj.run()
                    if not ret:
                        tc.logger.error("The execution of testcase %s failed" \
                                % name)
                        _ret = False
                ret = func_obj.cleanup()
                if not ret:
                    tc.logger.error("The cleanup of %s failed" % name)
                    _ret = False
            self.assertTrue(_ret, "Testcase %s failed" % name)
            inject_gluster_logs(name)
            tc.logger.info("Ending the test: %s" % name)
            return _ret

        testcases[name] = wrapper
        if not global_mode and tc_config is not None:
            for voltype in tc_config['runs_on_volumes']:
                if voltype not in test_list:
                    test_list[voltype] = []
                if not tc_config['reuse_setup']:
                    test_list.insert(0, name)
                else:
                    test_list[voltype].append(name)
        return wrapper

    return decorator


def distaf_finii():
    """
        The fini() function which closes all connection to the servers
    """
    tc.fini()
