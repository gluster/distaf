from distaf.util import tc, testcase
from distaf.distaf_base_class import DistafTestClass


@testcase("this_should_pass")
class get_hostname(DistafTestClass):
    """
        runs_on_volumes: ALL
        runs_on_protocol: [ glusterfs, nfs, cifs ]
        reuse_setup: True
    """
    def setup(self):
        return True

    def run(self):
        tc.logger.info("Testing connection and command exec")
        ret = 0
        ret, _, _ = tc.run(self.nodes[0], "hostname")
        if ret != 0:
            tc.logger.error("hostname command failed")
            return False
        else:
            return True

    def teardown(self):
        return True

    def cleanup(self):
        return True

@testcase("this_should_fail")
class going_to_fail(DistafTestClass):
    """
        runs_on_volumes: ALL
        runs_on_protocol: [ glusterfs, nfs ]
        reuse_setup: True
    """
    def setup(self):
        return True

    def run(self):
        tc.logger.info("Testing fail output")
        ret = 0
        ret, _, _ = tc.run(self.nodes[0], "false")
        if ret != 0:
            tc.logger.error("false command failed")
            return False
        else:
            return True

    def teardown(self):
        return True

    def cleanup(self):
        return True
