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


import os
import re
import time
from distaf.util import tc
from distaf.peer_ops import peer_probe
from distaf.volume_ops import create_volume
from distaf.gluster_init import env_setup_servers
from distaf.mount_ops import mount_volume, umount_volume
from distaf.gluster_init import start_glusterd, stop_glusterd


def set_sync_mode(mvol, svol, mode, mnode='', snode=''):
    """
        Sets the sync mode for the geo-rep session
        mastervol, slavevol and mode are mandatory parameters
        slave node is optional. Will default to first slave node
        master node is also optioanl. Will default to first master node
        Returns True if the operation is successfull
        Returns False if the operation fails
    """
    if mnode == '':
        mnode = tc.gm_nodes[0]
    if snode == '':
        snode = tc.gs_nodes[0]
    if mode == 'tarssh':
        cmd_string = 'use-tarssh true'
    elif mode == 'rsync':
        cmd_string = '\!use-tarssh'
    else:
        tc.logger.error("sync mode %s is not supported" % mode)
        return False
    mountbroker = ''
    if tc.config_data['MOUNTBROKER'] == 'True':
        mountbroker = '%s@' % tc.config_data['GEO_USER']
    try:
        temp = tc.sync_mode
    except AttributeError:
        tc.sync_mode = 'rsync'
    if mode == tc.sync_mode:
        tc.logger.debug("sync mode is already set to %s" % mode)
        return True
    cmd = "gluster volume geo-replication %s %s%s::%s config %s" % \
           (mvol, mountbroker, snode, svol, cmd_string)
    ret, _, _ = tc.run(mnode, cmd)
    if ret == 0:
        tc.logger.debug("sync mode set to %s was successfull" % mode)
        tc.sync_mode = mode
        return True
    else:
        tc.logger.error("Unable to set the sync mode to %s" % mode)
        return False


def set_change_detector(mvol, svol, detector, mnode='', snode=''):
    """
        Sets the change detector of the geo-rep session

        Returns False if the operation failed
        Returns True if the operation is successfull
    """
    if mnode == '':
        mnode = tc.gm_nodes[0]
    if snode == '':
        snode = tc.gs_nodes[0]
    mountbroker = ''
    if tc.config_data['MOUNTBROKER'] == 'True':
        mountbroker = '%s@' % tc.config_data['GEO_USER']
    try:
        temp = tc.change_detector
    except AttributeError:
        tc.change_detector = 'changelog'
    if detector == tc.change_detector:
        tc.logger.debug("The change detector is already set to %s" \
                       % detector)
        return True
    cmd = "gluster volume geo-replication %s %s%s::%s config change_detector \
%s" % (mvol, mountbroker, snode, svol, detector)
    ret, _, _ = tc.run(mnode, cmd)
    if ret == 0:
        tc.logger.debug("Change detector successfully set to %s" % detector)
        tc.change_detector = detector
        return True
    else:
        tc.logger.error("Unable to set the change detector to %s" % detector)
        return False


def create_geo_rep_data(client, path, fop, user='', async=False):
    """
        Creates the geo-rep data on the path as per geo-rep specs
    """
    if os.path.realpath(path) == '/':
        tc.logger.error("The resolved path can not be '/'")
        return False
    conf_dict = tc.config_data
    dir_struct = conf_dict['DIR_STRUCT']
    user = conf_dict['GEO_USER']
    file_type = conf_dict['FILE_TYPE']
    num_multi = conf_dict['FILES_PER_DIR']
    num_single = conf_dict['NUM_FILES_SING']
    num_threads = conf_dict['NUM_THREADS']
    maxsize = conf_dict['SIZE_MAX']
    minsize = conf_dict['SIZE_MIN']
    breadth = conf_dict['DIRS_BREADTH']
    depth = conf_dict['DIRS_DEPTH']
    if dir_struct == 'multi':
        cmd = "crefi --multi -n %d -b %d -d %d --max=%s --min=%s --random \
-T %d -t %s --fop=%s %s 1>/dev/null 2>&1" % (int(num_multi), int(breadth), \
int(depth), maxsize, minsize, int(num_threads), file_type, fop, path)
    elif dir_struct == 'single':
        cmd = "crefi -n %d --max=%s --min=%s --random -T %d -t %s --fop=%s %s \
1>/dev/null 2>&1" % (int(num_single), maxsize, minsize, int(num_threads), \
file_type, fop, path)
    else:
        tc.logger.error("Unknown fop or dir structure")
        return False
    if fop == 'rm':
        cmd = "rm -rf %s/*" % path
    if async:
        ret_obj = tc.run_async(client, cmd)
        return ret_obj
    else:
        ret, _, _ = tc.run(client, cmd)
        if ret != 0:
            return False
        else:
            return True


def check_geo_filecount_status(master, mastervol, slave, slavevol, \
        timeout=1200, mclient='', sclient=''):
    """
        checks the number of files in master and slave

        Returns True if number of files are same in master and slave
        Returns False if number of files differ in master and slave
    """
    if mclient == '':
        mclient = tc.clients[0]
    if sclient == '':
        sclient = tc.clients[0]
    master_mount = '/mnt/master'
    slave_mount = '/mnt/slave'
    retm, _, _ = mount_volume(mastervol, mpoint=master_mount, \
            mserver=master, mclient=mclient)
    rets, _, _ = mount_volume(slavevol, mpoint=slave_mount, \
            mserver=slave, mclient=sclient)
    if retm != 0 or rets != 0:
        tc.logger.error("Failed to mount the master or slave volume")
        return False
    rc = False
    while timeout >= 0:
        retm = tc.run_async(mclient, "find %s | wc -l" % master_mount)
        rets = tc.run_async(sclient, "find %s | wc -l" % slave_mount)
        retm.wait()
        rets.wait()
        retm = retm.value()
        rets = rets.value()
        tc.logger.debug("The number of files in master is %s" % int(retm[1]))
        tc.logger.debug("The number of files in slave is %s" % int(rets[1]))
        if retm[0] != 0 or rets[0] != 0:
            tc.logger.error("find returned error. Please check glusterfs logs")
        elif int(retm[1]) != int(rets[1]):
            tc.logger.debug("filecount doesn't match between master and slave")
        else:
            tc.logger.info("filecount of master and slave match")
            rc = True
            break
        time.sleep(120)
        timeout = timeout - 120
    umount_volume(mclient, master_mount)
    umount_volume(sclient, slave_mount)
    return rc


def check_geo_arequal_status(master, mastervol, slave, slavevol, \
        timeout=600, mclient='', sclient=''):
    """
        checks the arequal checksum of master and slave

        Returns True if arequal checksum matches between master and slave
        Returns False if arequal checksum differs between master and slave
    """
    if mclient == '':
        mclient = tc.clients[0]
    if sclient == '':
        sclient = tc.clients[0]
    master_mount = '/mnt/master'
    slave_mount = '/mnt/slave'
    retm, _, _ = mount_volume(mastervol, mpoint=master_mount, mserver=master, \
            mclient=mclient)
    rets, _, _ = mount_volume(slavevol, mpoint=slave_mount, mserver=slave, \
            mclient=sclient)
    if retm != 0 or rets != 0:
        tc.logger.error("Failed to mount the master or slave volume")
        return False
    rc = False
    while timeout >= 0:
        retm = tc.run_async(mclient, "/usr/local/bin/arequal-checksum -p %s" \
                % master_mount)
        rets = tc.run_async(sclient, "/usr/local/bin/arequal-checksum -p %s" \
                % slave_mount)
        retm.wait()
        rets.wait()
        retm = retm.value()
        rets = rets.value()
        tc.logger.debug("The arequal-checksum of master is %s" % retm[1])
        tc.logger.debug("The arequal-checksum of slave is %s" % rets[1])
        if retm[0] != 0 or rets[0] != 0:
            tc.logger.error("arequal returned error. Check glusterfs logs")
        elif retm[1] != rets[1]:
            tc.logger.debug("arequal-checksum does not match master and slave")
        else:
            tc.logger.info("arequal-checksum of master and slave match")
            rc = True
            break
        time.sleep(120)
        timeout = timeout - 120
    umount_volume(mclient, master_mount)
    umount_volume(sclient, slave_mount)
    return rc


def create_geo_passwordless_ssh(mnode, snode, gsuser=''):
    """
        Sets up the password less ssh between two specified nodes

        Returns True if successfull and False on failure
    """
    if gsuser == '':
        gsuser = 'root'
    loc = "/var/lib/glusterd/geo-replication/"
    mconn = tc.get_connection(mnode, user='root')
    sconn = tc.get_connection(snode, user=gsuser)
    tc.run(mnode, "ssh-keyscan %s >> /root/.ssh/known_hosts" % snode)
    if not mconn.modules.os.path.isfile('/root/.ssh/id_rsa'):
        if not mconn.modules.os.path.isfile('%s/secret.pem' % loc):
            tc.logger.debug("id_rsa not present. Generating with gsec_create")
            ret = tc.run(mnode, "gluster system:: execute gsec_create")
            if ret[0] != 0:
                tc.logger.error("Unable to generate the secret pem file")
                return False
        tc.logger.debug("Copying the secret.pem to id_rsa")
        mconn.modules.shutil.copyfile("%s/secret.pem" % loc, \
                "/root/.ssh/id_rsa")
        mconn.modules.os.chmod("/root/.ssh/id_rsa", 0600)
        tc.logger.debug("Copying the secret.pem.pub to id_rsa.pub")
        mconn.modules.shutil.copyfile("%s/secret.pem.pub" % loc, \
                "/root/.ssh/id_rsa.pub")
    try:
        slocal = sconn.modules.os.path.expanduser('~')
        sfh = sconn.builtin.open("%s/.ssh/authorized_keys" % slocal, "a")
        with mconn.builtin.open("/root/.ssh/id_rsa.pub", 'r') as f:
            for line in f:
                sfh.write(line)
    except:
        tc.logger.error("Unable to establish passwordless ssh %s@%s to %s@%s" \
                % ('root', mnode, gsuser, snode))
        return False
    finally:
        sfh.close()
        mconn.close()
        sconn.close()
    tc.logger.debug("Password less ssh setup from %s@%s to %s@%s is %s" \
            % ('root', mnode, gsuser, snode, 'successfull'))
    return True


def geo_rep_setup_metavolume(mvol, svol, slave, servers=''):
    """
        Sets up a meta volume for geo-replication consumption

        @ parameter:
            * mvol - Master volume name
            * svol - Slave volume name
            * slave - slave host node
            * servers - Cluster of nodes where meta-volume should be created
                        and mounted

        @ returns:
            True upon successfully configuring meta-volume
            False otherwise
    """
    if servers == '':
        servers = tc.gm_nodes
    meta_volname = "gluster_shared_storage"
    ret = setup_meta_vol(servers)
    if not ret:
        tc.logger.error("meta volume config failed. Aborting")
        return False
    mountbroker = ''
    if tc.config_data['MOUNTBROKER'] == "True":
        mountbroker = "%s@" % tc.config_data['GEO_USER']
    config_cmd = "gluster volume geo-replication %s %s%s::%s config \
use_meta_volume true" % (mvol, mountbroker, slave, svol)
    ret = tc.run(servers[0], config_cmd)
    if ret[0] != 0:
        tc.logger.error("Unable to config the geo-rep session to use metavol")
        return False
    return True


def setup_geo_rep_mountbroker():
    """
        setup the geo-rep mountbroker session
    """
    mountbroker = tc.config_data['GEO_USER']
    ggroup = tc.config_data['GEO_GROUP']
    slavevol = tc.config_data['SLAVEVOL']
    glusterd_volfile_cmd = \
"cp /etc/glusterfs/glusterd.vol /tmp/glusterd.vol && \
sed -i '/end-volume/d' /tmp/glusterd.vol && \
sed -i '/geo-replication/d' /tmp/glusterd.vol && \
sed -i '/mountbroker/d' /tmp/glusterd.vol && \
sed -i '/rpc-auth-allow-insecure/d' /tmp/glusterd.vol && \
echo \"    option mountbroker-root /var/mountbroker-root\" >> \
/tmp/glusterd.vol && \
echo \"    option mountbroker-geo-replication.%s %s\" >> /tmp/glusterd.vol && \
echo \"    option geo-replication-log-group %s\" >> /tmp/glusterd.vol && \
echo \"    option rpc-auth-allow-insecure on\" >> /tmp/glusterd.vol && \
echo \"end-volume\" >> /tmp/glusterd.vol && \
cp /tmp/glusterd.vol /etc/glusterfs/glusterd.vol" % \
(mountbroker, slavevol, ggroup)
    for slave in tc.gs_nodes:
        ret = tc.add_user(slave, mountbroker, group=ggroup)
        if not ret:
            tc.logger.error("Unable to add %s to group" % mountbroker)
        ret, _, _ = tc.run(slave, "mkdir /var/mountbroker-root")
        if ret != 0:
            tc.logger.error("Unable to create directory")
        ret, _, _ = tc.run(slave, "chmod 0711 /var/mountbroker-root")
        if ret != 0:
            tc.logger.error("cannot change permission")
        ret = stop_glusterd([slave])
        if not ret:
            tc.logger.error("gluster stop failed")
            return False
        ret, _, _ = tc.run(slave, glusterd_volfile_cmd)
        if ret != 0:
            tc.logger.error("Unable to edit the glusterd volfile")
            return False
        ret = start_glusterd([slave])
        if not ret:
            tc.logger.error("Unable to start glusterd. Exiting")
            return False
    return True


def setup_geo_rep_session(setup=''):
    """
        Does initial setup and creates a geo-rep session and updates a global
        variable upon success. Other testcases, can skip the setup part if the
        global variable is set

        If the 'setup' is not set, a geo-rep session setup between master
        cluster and slave cluster

        If the 'setup' is set to 'fanout', the session is setup between master
        cluster and slave clusters

        If the 'setup' is set to 'cascaded' then a cascaded geo-rep session
        is setup between master to intermediate master(s) to slave cluster
    """
    mastervol = tc.config_data['MASTERVOL']
    mnode = tc.gm_nodes[0]
    dist = tc.config_data['DIST_COUNT']
    rep = tc.config_data['REP_COUNT']
    stripe = tc.config_data['STRIPE']
    trans = tc.config_data['TRANS_TYPE']
    guser = tc.config_data['GEO_USER']
    mountbroker = ''
    rc = True
    try:
        if tc.global_flag['setup_fs_done']:
            tc.logger.debug("bricks are already formatted. Skipping setup_fs")
    except KeyError:
        tc.logger.debug("The bricks are not formatted yet. Execute setup_fs")
        tc.global_flag['setup_fs_done'] = False
    if not tc.global_flag['setup_fs_done']:
        ret = env_setup_servers()
        if not ret:
            tc.logger.error("env_setup_servers failed. Aborting tests...")
            return False
    ret = start_glusterd()
    if not ret:
        tc.logger.error("Unable to start glusterd. Exiting")
        return False
    ret = peer_probe(mnode, tc.gm_nodes[1:])
    if not ret:
        tc.logger.error("peer probe failed in master cluster")
        return False
    ret = create_volume(mastervol, dist, rep, stripe, trans, \
            servers=tc.gm_nodes)
    if 0 != ret[0]:
        tc.logger.error("Unable to create geo-rep master volume. "
                "Please check the gluster logs")
        return False
    ret = start_volume(mastervol, mnode)
    if not ret:
        tc.logger.error("volume start master volume failed")
        return False
    if setup == '':
        slavevol = tc.config_data['SLAVEVOL']
        snode = tc.gs_nodes[0]
        ret = peer_probe(snode, tc.gs_nodes[1:])
        if not ret:
            tc.logger.error("peer probe failed in slave cluster")
            return False
        ret = create_volume(slavevol, dist, rep, stripe, trans, \
                servers=tc.gs_nodes)
        if ret[0] != 0:
            tc.logger.error("Unable to create the slave volume")
            return False
        ret = start_volume(slavevol, snode)
        if not ret:
            tc.logger.error("volume start failed in slave cluster")
            return False
        if tc.config_data['MOUNTBROKER'] == 'True':
            mountbroker = '%s@' % guser
            ret = setup_geo_rep_mountbroker()
            if not ret:
                tc.logger.error("mountbroker setup failed. Aborting...")
                return False
        tc.run(mnode, "gluster system execute gsec_create")
        ret = create_geo_passwordless_ssh(mnode, snode, guser)
        if not ret:
            return False
        ret = tc.run(mnode, \
              "gluster volume geo-replication %s %s%s::%s create push-pem" \
              % (mastervol, mountbroker, snode, slavevol))
        if ret[0] != 0:
            rc = False
        if tc.config_data['MOUNTBROKER'] == 'True':
            ret = tc.run(snode, \
"/usr/libexec/glusterfs/set_geo_rep_pem_keys.sh %s %s %s" % \
(guser, mastervol, slavevol))
            if ret[0] != 0:
                tc.logger.error("Couldn't set pem keys in slave")
                rc = False
        if tc.config_data['USE_META_VOL'] == "True":
            ret = geo_rep_setup_metavolume(mastervol, slavevol, snode)
            if not ret:
                tc.logger.error("Unable to setup meta-volume for geo-rep")
                rc = False
        syn_mode = tc.config_data['GEO_SYNC_MODE']
        ret = set_sync_mode(mastervol, slavevol, syn_mode)
        if not ret:
            tc.logger.error("Unable to set the sync mode to %s" % sync_mode)
            rc = False
        ret = tc.run(mnode, "gluster volume geo-replication %s %s%s::%s \
start" % (mastervol, mountbroker, snode, slavevol))
        if ret[0] != 0:
            rc = False
        ret = tc.run(mnode, "gluster volum geo-replication %s %s%s::%s \
status" % (mastervol, mountbroker, snode, slavevol))
        if ret[0] != 0 or re.search(r'faulty', ret[1] + ret[2]):
            tc.logger.error("geo-rep status faulty. Please check the logs")
            rc = False
        time.sleep(60)
        ret = tc.run(mnode, "gluster volum geo-replication %s %s%s::%s \
status" % (mastervol, mountbroker, snode, slavevol))
        if ret[0] != 0 or re.search(r'faulty', ret[1] + ret[2]):
            tc.logger.error("geo-rep session faulty after 60 seconds")
            rc = False
        tc.geo_rep_setup = True
    elif setup == 'fanout':
        # The support for fan-out and cascaded will be added in future
        pass
    elif setup == 'cascaded':
        # The support for fan-out and cascaded will be added future
        pass
    else:
        tc.logger.error("The setup %s is not supported" % setup)
        return False
    return rc


def geo_rep_basic_test(fop, cd='changelog', history=False):
    """
        Changelog tests for geo-rep
    """
    mountbroker = ''
    guser = tc.config_data['GEO_USER']
    if tc.config_data['MOUNTBROKER'] == 'True':
        mountbroker = '%s@' % guser
    try:
        temp = tc.geo_rep_setup
    except AttributeError:
        tc.geo_rep_setup = False
    if not tc.geo_rep_setup:
        ret = setup_geo_rep_session()
        if not ret:
            tc.logger.error("Unable to create geo_rep session. Skipping test")
            return False
    mastervol = tc.config_data['MASTERVOL']
    mountpoint = tc.config_data['MOUNTPOINT']
    mnode = tc.gm_nodes[0]
    snode = tc.gs_nodes[0]
    slavevol = tc.config_data['SLAVEVOL']
    if len(tc.clients) >= 2:
        mclient = tc.clients[0]
        sclient = tc.clients[1]
    else:
        mclient = tc.clients[0]
        sclient = tc.clients[0]
    ret = set_change_detector(mastervol, slavevol, cd)
    if not ret:
        tc.logger.error("change detector set failed. Marking test case FAIL")
        return False
    if history:
        ret = tc.run(mnode, "gluster volume geo-replication %s %s%s::%s stop" \
                    % (mastervol, mountbroker, snode, slavevol))
        if ret[0] != 0:
            tc.logger.error("Unable to stop geo-rep session in history tests")
            return False
    ret, _, _ = mount_volume(mastervol, tc.config_data['MOUNT_TYPE'], \
            mountpoint, mnode, mclient)
    if ret != 0:
        tc.logger.error("Unable to mount the volume. Marking the test as FAIL")
        return False
    ret = create_geo_rep_data(mclient, mountpoint, fop, guser)
    if not ret:
        tc.logger.error("Data creation failed. Marking the test as FAIL")
        return False
    if history:
        ret = tc.run(mnode, "gluster volume geo-replication %s %s%s::%s \
start" % (mastervol, mountbroker, snode, slavevol))
        if ret[0] != 0:
            tc.logger.error("Unable to start geo-rep session in history tests")
            return False
    ret = check_geo_filecount_status(mnode, mastervol, snode, slavevol, \
                                     mclient=mclient, sclient=sclient)
    if not ret:
        tc.logger.error("filecount does not match. Marking testcase as FAIL")
        return False
    ret = check_geo_arequal_status(mnode, mastervol, snode, slavevol, \
                                   mclient=mclient, sclient=sclient)
    if not ret:
        tc.logger.error("arequal checksum do not match. Marking the test FAIL")
        return False
    return True
