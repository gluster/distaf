#  This file is part of DiSTAF
#  Copyright (C) 2015-2016  Red Hat, Inc. <http://www.redhat.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


from types import FunctionType
from distaf.client_rpyc import BigBang
from distaf.config_parser import get_global_config, get_testcase_config


testcases = {}
test_list = {}
test_seq = []
test_mounts = {}
globl_configs = {}
global_mode = None
tc = None


def distaf_init(config_file="config.yml"):
    """
        The distaf init function which calls the  BigBang
    """
    global globl_configs, global_mode, tc
    globl_configs = get_global_config(config_file)
    global_mode = globl_configs['global_mode']
    tc = BigBang(globl_configs)
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
        tc_config = get_testcase_config(func.__doc__)

        def wrapper(self):
            tc.logger.info("Starting the test: %s" % name)
            voltype, mount_proto = test_seq.pop(0)
            inject_gluster_logs("%s_%s" % (voltype, name))
            _ret = True
            globl_configs['reuse_setup'] = tc_config['reuse_setup']
            globl_configs.update(tc_config)
            globl_configs['voltype'] = voltype
            globl_configs['mount_proto'] = mount_proto
            if isinstance(func, FunctionType):
                _ret = func()
            else:
                try:
                    func_obj = func(globl_configs)
                    ret = func_obj.setup()
                    if not ret:
                        tc.logger.error("The setup of %s failed" % name)
                        _ret = False
                    if _ret:
                        ret = func_obj.run()
                        if not ret:
                            tc.logger.error("The execution of testcase %s " \
                                    "failed" % name)
                            _ret = False
                    ret = func_obj.teardown()
                    if not ret:
                        tc.logger.error("The teardown of %s failed" % name)
                        _ret = False
                    if len(test_seq) == 0 or voltype != test_seq[0][0]:
                        tc.logger.info("Last test case to use %s volume type" \
                                % voltype)
                        ret = func_obj.cleanup()
                        if not ret:
                            tc.logger.error("The cleanup of volume %s failed" \
                                    % name)
                            _ret = False
                except:
                    tc.logger.exception("Exception while running %s" % name)
                    _ret = False
            self.assertTrue(_ret, "Testcase %s failed" % name)
            inject_gluster_logs("%s_%s" % (voltype, name))
            tc.logger.info("Ending the test: %s" % name)
            return _ret

        testcases[name] = wrapper
        if not global_mode and tc_config is not None:
            for voltype in tc_config['runs_on_volumes']:
                if voltype not in test_list:
                    test_list[voltype] = []
                if not tc_config['reuse_setup']:
                    test_list[voltype].insert(0, name)
                else:
                    test_list[voltype].append(name)
            test_mounts[name] = tc_config['runs_on_protocol']
        return wrapper

    return decorator


def distaf_finii():
    """
        The fini() function which closes all connection to the servers
    """
    tc.fini()
