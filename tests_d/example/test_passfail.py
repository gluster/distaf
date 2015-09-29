from distaf.util import tc, testcase

@testcase("this_should_pass")
def get_hostname():
    tc.logger.info("Testing connection and command exec")
    mnode = tc.servers[0]
    ret, _, _ = tc.run(mnode, "hostname")

    if ret != 0:
        tc.logger.error("hostname command failed")

        return False
    else:
        return True

@testcase("this_should_fail")
def going_to_fail():
    tc.logger.info("Testing fail output")
    mnode = tc.servers[0]
    ret, _, _ = tc.run(mnode, "false")

    if ret != 0:
        tc.logger.error("false command failed")

        return False
    else:
        return True
