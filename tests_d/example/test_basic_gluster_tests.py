import time
from libs.util import tc, testcase, start_glusterd, peer_probe
from libs.util import create_volume, mount_volume

@testcase("gluster_basic_test")
def gluster_basic_test():
    tc.logger.info("Testing gluster volume create and mounting")
    ret = start_glusterd()
    if not ret:
        tc.logger.error("Unable to start glusterd. Please check the logs")
        return False
    mnode = tc.nodes[0]
    client = tc.clients[0]
    volname = tc.config_data['VOLNAME']
    dist = tc.config_data['DIST_COUNT']
    rep = tc.config_data['REP_COUNT']
    trans = tc.config_data['TRANS_TYPE']
    mountpoint = tc.config_data['MOUNTPOINT']
    mount_type = tc.config_data['MOUNT_TYPE']
    rc = True
    ret = peer_probe()
    if not ret:
        tc.logger.error("peer probe to one or more machines failed")
        return False
    ret, out, err = create_volume(volname, dist, rep, trans=trans)
    if ret != 0:
        tc.logger.error("volume create failed")
        rc = False
    ret, _, _ = tc.run(mnode, "gluster volume start %s" % volname)
    if ret != 0:
        tc.logger.error("Volume start failed")
        rc = False
    time.sleep(5)
    tc.run(mnode, "gluster volume status %s" % volname)
    ret, _, _ = mount_volume(volname, mount_type, mountpoint, mclient=client)
    if ret != 0:
        tc.logger.error("mounting volume %s failed" % volname)
        rc = False
    if rc:
        ret, _, _ = tc.run(client, "cp -r /etc %s" % mountpoint)
        if ret != 0:
            tc.logger.error("cp failed on the mountpoint")
            rc = False
        tc.run(client, "umount %s || umount -l %s" % (mountpoint, mountpoint))
    tc.run(mnode, "gluster --mode=script volume stop %s" % volname)
    tc.run(mnode, "gluster --mode=script volume delete %s" % volname)
    return rc
