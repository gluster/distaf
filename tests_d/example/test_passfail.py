from distaf.util import tc, testcase


@testcase("this_should_pass")
def get_hostname():
    """
        runs_on_volumes: ALL
        runs_on_protocol: [ glusterfs, nfs, cifs ]
        reuse_setup: True
    """
    tc.logger.info("Testing connection and command exec")
    mnode = tc.servers[0]
    ret, _, _ = tc.run(mnode, "hostname")
    ret = 0
    if ret != 0:
        tc.logger.error("hostname command failed")
        return False
    else:
        return True


@testcase("this_should_fail")
def going_to_fail():
    """
        runs_on_volumes: [ dist, dist-rep, rep ]
        runs_on_protocol: [ glusterfs, nfs ]
        reuse_setup: True
    """
    tc.logger.info("Testing fail output")
    mnode = tc.servers[0]
    ret, _, _ = tc.run(mnode, "false")
    ret = 0
    if ret != 0:
        tc.logger.error("false command failed")
        return False
    else:
        return True
