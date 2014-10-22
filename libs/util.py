import re
from client_rpyc import *
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
    config_dict = {}
    if 'MOUNT_TYPE' in os.environ:
        config_dict['mount_type'] = os.environ['MOUNT_TYPE']
    else:
        config_dict['mount_type'] = 'glusterfs'
    if 'GEO_CLIENT_USER' in os.environ:
        config_dict['guser'] = os.environ['GEO_CLIENT_USER']
    else:
        config_dict['guser'] = 'root'
    if 'FILE_TYPE' in os.environ:
        config_dict['file_type'] = os.environ['FILE_TYPE']
    else:
        config_dict['file_type'] = 'text'
    if 'DIR_STRUCT' in os.environ:
        config_dict['dir_struct'] = os.environ['DIR_STRUCT']
    else:
        config_dict['dir_struct'] = 'multi'
    if 'NUM_FILES_MULTI' in os.environ:
        config_dict['nf'] = os.environ['NUM_FILES_MULTI']
    else:
        config_dict['nf'] = 5
    if 'NUM_FILES_SINGLE' in os.environ:
        config_dict['ns'] = os.environ['NUM_FILES_SINGLE']
    else:
        config_dict['ns'] = 1000
    if 'NUM_THREADS' in os.environ:
        config_dict['nt'] = os.environ['NUM_THREADS']
    else:
        config_dict['nt'] = 5
    if 'DIRS_BREADTH' in os.environ:
        config_dict['breadth'] = os.environ['DIRS_BREADTH']
    else:
        config_dict['breadth'] = 5
    if 'DIRS_DEPTH' in os.environ:
        config_dict['depth'] = os.environ['DIRS_DEPTH']
    else:
        config_dict['depth'] = 5
    if 'SIZE_MIN' in os.environ:
        config_dict['minsize'] = os.environ['SIZE_MIN']
    else:
        config_dict['minsize'] = '5k'
    if 'SIZE_MAX' in os.environ:
        config_dict['maxsize'] = os.environ['SIZE_MAX']
    else:
        config_dict['maxsize'] = '10k'
    if 'VOLNAME' in os.environ:
        config_dict['volname'] = os.environ['VOLNAME']
    else:
        config_dict['volname'] = 'testvol'
    if 'DISTCOUNT' in os.environ:
        config_dict['dist'] = os.environ['DISTCOUNT']
    else:
        config_dict['dist'] = 2
    if 'REPCOUNT' in os.environ:
        config_dict['rep'] = os.environ['REPCOUNT']
    else:
        config_dict['rep'] = 2
    if 'STRIPECOUNT' in os.environ:
        config_dict['stripe'] = os.environ['STRIPECOUNT']
    else:
        config_dict['stripe'] = 1
    if 'TRANSTYPE' in os.environ:
        config_dict['transport'] = os.environ['TRANSTYPE']
    else:
        config_dict['transport'] = 'tcp'
    if 'MOUNTPOINT' in os.environ:
        config_dict['mountpoint'] = os.environ['MOUNTPOINT']
    else:
        config_dict['mountpoint'] = '/mnt/glusterfs'
    if param == None:
        return config_dict
    elif param in config_dict.keys():
        return config_dict[param]
    else:
        return False
