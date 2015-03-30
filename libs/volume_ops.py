import re
import time
from libs.util import tc
from libs.gluster_init import env_setup_servers, start_glusterd
from libs.peer_ops import peer_probe

"""
    This file contains the gluster volume operations like create volume,
    start/stop volume
"""

def create_volume(volname, dist, rep=1, stripe=1, trans='tcp', servers='', \
        snap=True, disp=1, dispd=1, red=1):
    """
        Create the gluster volume specified configuration
        volname and distribute count are mandatory argument
    """
    global tc
    if servers == '':
        servers = tc.nodes[:]
    dist = int(dist)
    rep = int(rep)
    stripe = int(stripe)
    disp = int(disp)
    dispd = int(dispd)
    red = int(red)
    dispc = 1

    if disp != 1 and dispd != 1:
        tc.logger.error("volume can't have both disperse and disperse-data")
        return (-1, None, None)
    if disp != 1:
        dispc = int(disp)
    elif dispd != 1:
        dispc = int(dispd) + int(red)

    number_of_bricks = dist * rep * stripe * dispc
    replica = stripec = disperse = disperse_data = redundancy = ''
    brick_root = '/bricks'
    n = 0
    tempn = 0
    bricks_list = ''
    rc = tc.run(servers[0], "gluster volume info | egrep \"^Brick[0-9]+\"", \
            verbose=False)
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
    if disp != 1:
        disperse = "disperse %d" % disp
        redundancy = "redundancy %d" % red
    elif dispd != 1:
        disperse_data = "disperse-data %d" % dispd
        redundancy = "redundancy %d" % red

    ret = tc.run(servers[0], "gluster volume create %s %s %s %s %s %s %s %s \
--mode=script" % (volname, replica, stripec, disperse, disperse_data, \
redundancy, ttype, bricks_list))
    return ret

def start_volume(volname, mnode='', force=False):
    """
        Starts the gluster volume
        Returns True if success and False if failure
    """
    if mnode == '':
        mnode = tc.nodes[0]
    frce = ''
    if force:
        frce = 'force'
    ret = tc.run(mnode, "gluster volume start %s %s" % (volname, frce))
    if ret[0] != 0:
        return False
    return True


def stop_volume(volname, mnode='', force=False):
    """
        Stops the gluster volume
        Returns True if success and False if failure
    """
    if mnode == '':
        mnode = tc.nodes[0]
    frce = ''
    if force:
        frce = 'force'
    ret = tc.run(mnode, "gluster volume stop %s %s --mode=script" \
            % (volname, frce))
    if ret[0] != 0:
        return False
    return True


def delete_volume(volname, mnode=''):
    """
        Deletes the gluster volume
        Returns True if success and False if failure
    """
    if mnode == '':
        mnode = tc.nodes[0]
    ret = tc.run(mnode, "gluster volume delete %s --mode=script" % volname)
    if ret[0] != 0:
        return False
    try:
        del tc.global_flag[volname]
    except KeyError:
        pass
    return True


def setup_vol(volname='', dist=1, rep=1, dispd=1, red=1, stripe=1, trans='', \
        servers=''):
    """
        Setup a gluster volume for testing.
        It first formats the back-end bricks and then creates a
        trusted storage pool by doing peer probe. And then it creates
        a volume of specified configuration.

        When the volume is created, it sets a global flag to indicate
        that the volume is created. If another testcase calls this
        function for the second time with same volume name, the function
        checks for the flag and if found, will return True.

        Returns True on success and False for failure.
    """
    if volname == '':
        volname = tc.config_data['VOLNAME']
    if dist == 1:
        dist = tc.config_data['DIST_COUNT']
    if rep == 1:
        rep = tc.config_data['REP_COUNT']
    if dispd == 1:
        dispd = tc.config_data['DISPERSE']
    if red == 1:
        red = tc.config_data['REDUNDANCY']
    if stripe == 1:
        stripe = tc.config_data['STRIPE']
    if trans == '':
        trans = tc.config_data['TRANS_TYPE']
    if servers == '':
        servers = tc.nodes
    try:
        if tc.global_flag[volname] == True:
            tc.logger.debug("The volume %s is already created. Returning..." \
                    % volname)
            return True
    except KeyError:
        tc.logger.info("The volume %s is not present. Creating it" % volname)
    ret = env_setup_servers(servers=servers)
    if not ret:
        tc.logger.error("Formatting backend bricks failed. Aborting...")
        return False
    ret = start_glusterd(servers)
    if not ret:
        tc.logger.error("glusterd did not start in at least one server")
        return False
    ret = peer_probe(servers[0], servers[1:])
    if not ret:
        tc.logger.error("Unable to peer probe one or more machines")
        return False
    if rep != 1 and dispd != 1:
        tc.logger.warning("Both replica count and disperse count is specified")
        tc.logger.warning("Ignoring the disperse and using the replica count")
        dispd = 1
        red = 1
    ret = create_volume(volname, dist, rep, stripe, trans, servers, \
            dispd=dispd, red=red)
    if ret[0] != 0:
        tc.logger.error("Unable to create volume %s" % volname)
        return False
    time.sleep(4)
    ret = start_volume(volname, servers[0])
    if not ret:
        tc.logger.error("volume start %s failed" % volname)
        return False
    tc.global_flag[volname] = True
    return True


def get_service_status(volname, services="ALL", servers=''):
    """
        get the service status of each service as displayed by the
        gluster volume status
    """
    if servers == '':
        servers = tc.nodes
    if services == "ALL":
        services = ["NFS", "Quota", "Self-heal", "Brick"]
    else:
        services = single_element_list(services)
        servers = single_element_list(servers)
    for service in services:
        print service
        flag = tc.run(servers[0], "gluster vol status %s | grep %s " \
                % (volname, service))
        if flag[0] == 0:
            flag = tc.run(servers[0], "gluster vol status %s | grep %s | egrep \
'[[:space:]]+N[[:space:]]+'" % (volname, service))
            if flag[0] == 0:
                for server in servers:
                    if service != "Brick" and server == servers[0]:
                        server = "localhost"
                    if re.search(server, flag[1]):
                        return False
        # If service is not listed in vol status return false
        else:
            return False
    return True

def single_element_list(input):
    if not isinstance(input, list):
        input = [input]
    return input
