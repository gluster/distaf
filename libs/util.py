import os
import re
from client_rpyc import big_bang

testcases = []
tc = big_bang()

def testcase(name):
    global testcases
    def decorator(func):
        def wrapper(self):
            ret = func()
            self.assertTrue(ret, "Testcase %s failed" % name)
            return ret
        testcases.append((name, wrapper))
        return wrapper
    return decorator


def finii():
    tc.fini()

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

def get_config_data(param=None):
    """
        Gets all the config data from the environmental variables

        Returns the value of requested parameter
        If nothing is requested the whole dict is sent
        If the requested parameter does not exist, the False is returned
    """
    config_dict = {
        'VOLNAME'         : 'testvol',
        'DIST_COUNT'      : 2,
        'REP_COUNT'       : 2,
        'STRIPE'          : 1,
        'TRANS_TYPE'      : 'tcp',
        'MOUNT_TYPE'      : 'glusterfs',
        'MOUNTPOINT'      : '/mnt/glusterfs',
        'GEO_USER'        : 'root',
        'FILE_TYPE'       : 'text',
        'DIR_STRUCT'      : 'multi',
        'NUM_FILES_MULTI' : 5,
        'NUM_FILES_SING'  : 1000,
        'NUM_THREADS'     : 5,
        'DIRS_BREADTH'    : 5,
        'DIRS_DEPTH'      : 5,
        'SIZE_MIN'        : '5k',
        'SIZE_MAX'        : '10k' }
    for conf in config_dict.keys():
        if conf in os.environ:
            config_dict[conf] = os.environ[conf]
    tc.config_data = config_dict
    if param == None:
        return config_dict
    elif param in config_dict.keys():
        return config_dict[param]
    else:
        return False

get_config_data()
