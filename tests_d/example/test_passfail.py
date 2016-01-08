from distaf.util import tc, testcase


@testcase("this_should_pass")
class get_hostname():
    """
        runs_on_volumes: ALL
        runs_on_protocol: [ glusterfs, nfs, cifs ]
        reuse_setup: True
    """
    def run(self):
        tc.logger.info("Testing connection and command exec")
        ret, _, _ = tc.run(self.mnode, "hostname")
        ret = 0
        if ret != 0:
            tc.logger.error("hostname command failed")
            return False
        else:
            return True


@testcase("this_should_fail")
class going_to_fail():
    """
        runs_on_volumes: [ dist, dist-rep, rep ]
        runs_on_protocol: [ glusterfs, nfs ]
        reuse_setup: True
    """
    def run(self):
        tc.logger.info("Testing fail output")
        ret, _, _ = tc.run(self.mnode, "false")
        ret = 0
        if ret != 0:
            tc.logger.error("false command failed")
            return False
        else:
            return True
