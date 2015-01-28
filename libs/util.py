import os
import re
from libs.client_rpyc import big_bang

testcases = []
tc = big_bang()

def testcase(name):
    def decorator(func):
        def wrapper(self):
            ret = func()
            self.assertTrue(ret, "Testcase %s failed" % name)
            return ret
        testcases.append((name, wrapper))
        return wrapper
    return decorator

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
    return ret

def mount_volume(volname, mtype='glusterfs', mpoint='/mnt/glusterfs', mserver='', mclient='', options=''):
    """
        Mount the gluster volume with specified options
        Takes the volume name as mandatory argument

        Returns a tuple of (returncode, stdout, stderr)
        Returns (0, '', '') if already mounted
    """
    global tc
    if mserver == '':
        mserver = tc.nodes[0]
    if mclient == '':
        mclient = tc.clients[0]
    if options != '':
        options = "-o %s" % options
    if mtype == 'nfs' and options != '':
        options = "%s,vers=3" % options
    elif mtype == 'nfs' and options == '':
        options = '-o vers=3'
    ret, _, _ = tc.run(mclient, "mount | grep %s | grep %s | grep \"%s\"" \
                % (volname, mpoint, mserver))
    if ret == 0:
        tc.logger.debug("Volume %s is already mounted at %s" \
        % (volname, mpoint))
        return (0, '', '')
    mcmd = "mount -t %s %s %s:%s %s" % (mtype, options, mserver,volname, mpoint)
    tc.run(mclient, "test -d %s || mkdir -p %s" % (mpoint, mpoint))
    return tc.run(mclient, mcmd)
