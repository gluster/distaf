import re
from client_rpyc import *
testcases = []
tc = big_bang()

def testcase(name):
    global testcases
    def decorator(func):
        def wrapper(self):
            ret = func(tc)
            self.assertTrue(ret, "Testcase %s failed" % name)
            return ret
        testcases.append((name, wrapper))
        return wrapper

    return decorator


def assert_true(var):
    try:
        assert var
    except AssertionError:
        #TODO: use a flag per testcase and update them
        pass

def assert_equal(var0, var1):
    try:
        assert var0 == var1
    except AssertionError:
        #TODO: use a flag per testcase and update them
        pass

def finii():
    tc.fini()

def get_vol_types():
    if 'VOLNAME' in os.environ:
        volname = os.environ['VOLNAME']
    else:
        volname = 'testvol'

    if 'DISTCOUNT' in os.environ:
        distcount = os.environ['DISTCOUNT']
    else:
        distcount = 2

    if 'REPCOUNT' in os.environ:
        repcount = os.environ['REPCOUNT']
    else:
        repcount = 2

    if 'STRIPECOUNT' in os.environ:
        strpcount = os.environ['STRIPECOUNT']
    else:
        strpcount = 1

    if 'TRANSTYPE' in os.environ:
        transtype = os.environ['TRANSTYPE']
    else:
        transtype = 'tcp'

    if 'MOUNTPOINT' in os.environ:
        mountpoint = os.environ['MOUNTPOINT']
    else:
        mountpoint = '/mnt/glusterfs'

    if 'MOUNT_TYPE' in os.environ:
        mounttype = os.environ['MOUNT_TYPE']
    else:
        mounttype = 'glusterfs'

    return (volname, distcount, repcount, strpcount, transtype, mountpoint, mounttype)

def create_volume(volname, dist, rep=1, stripe=1, trans='tcp', servers=[], snap=False):
    """
        Create the gluster volume specified configuration
        volname and distribute count are mandatory argument
    """
    global tc
    if servers == []:
        servers = tc.nodes[:]
    number_of_bricks = dist * rep * stripe
    replica = stripec = ''
    brick_root = '/bricks'
    n = 0
    tempn = 0
    bricks_list = ''
    rc = tc.run(servers[0], "gluster volume info | egrep \"^Brick[0-9]+\"")
    for i in range(0, number_of_bricks):
        if not snap:
            bricks_list = "%s %s:%s/%s_brick%d" % \
                (bricks_list, servers[n], brick_root, volname, i)
        else:
            sn = len(re.findall(servers[n], rc[1])) + tempn
            bricks_list = "%s %s:%s/brick%d/%s_brick%d" % \
            (bricks_list, servers[n], brick_root, sn, volname, i)
        if n < len(servers[:]) - 1:
            n = n + 1
        else:
            n = 0
            tempn = tempn + 1
    if rep != 1:
        replica = "replica %d" % rep
    if stripe != 1:
        stripec = "stripe %d" % stripe
    ttype = "transport %s" % trans
    ret = tc.run(servers[0], "gluster volume create %s %s %s %s %s" % \
                (volname, replica, stripec, ttype, bricks_list))
    assert_equal(ret[0], 0)
    return ret

def mount_volume(volname, mtype='glusterfs', mpoint='/mnt/glusterfs', mserver='', mclient='', options=''):
    """
        Mount the gluster volume with specified options
        Takes the volume name as mandatory argument

        Returns a tuple of (returncode, stdout, stderr)
    """
    global tc
    if mserver == '':
        mserver = tc.nodes[0]
    if mclient == '':
        mclient = tc.clients[0]
    if options != '':
        options = "-o %s" % options
    mcmd = "mount -t %s %s %s:%s %s" % (mtype, options, mserver,volname, mpoint)
    tc.run(mclient, "test -d %s || mkdir -p %s" % (mpoint, mpoint))
    return tc.run(mclient, mcmd)

def env_setup_servers():
    """
        Sets up the env for all the tests
        Install all the gluster bits and it's dependencies
        Installs the xfs bits and then formats the backend fs for gluster use

        Returns 0 on success and non-zero upon failing
    """
    global tc
    ret, rdict = tc.run_servers(". /usr/local/bin/qeTest_env_setup.sh \
                                && env_setup_servers")
    return ret
