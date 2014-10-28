import time
from libs.util import tc
from libs.util import testcase, create_volume, mount_volume, get_config_data

@testcase("gluster_basic_test")
def gluster_basic_test():
    tc.logger.info("Testing gluster volume create and mounting")
    ret, _ = tc.run_servers("pgrep glusterd || /etc/init.d/glusterd start")
    if not ret:
        tc.logger.error("Unable to start glusterd. Please check the logs")
        return False
    mnode = tc.nodes[0]
    conf_dict = get_config_data()
    volname = conf_dict['VOLNAME']
    rc = True
    for peer in tc.nodes[1:]:
        ret, out, err  = tc.run(mnode, "gluster peer probe %s" % peer)
        if ret != 0:
            rc = False
    if not rc:
        tc.logger.error("Peer probe failed in at least one node. Aborting test")
        return False
    ret, out, err = create_volume(volname, conf_dict['DIST_COUNT'], \
                    conf_dict['REP_COUNT'], trans=conf_dict['TRANS_TYPE'])
    if ret != 0:
        tc.logger.error("volume create failed")
        rc = False
    ret, _, _ = tc.run(mnode, "gluster volume start %s" % volname)
    if ret != 0:
        tc.logger.error("Volume start failed")
        rc = False
    time.sleep(5)
    tc.run(mnode, "gluster volume status %s" % volname)
    mountpoint = conf_dict['MOUNTPOINT']
    ret, _, _ = mount_volume(volname, conf_dict['MOUNT_TYPE'], mountpoint)
    if ret != 0:
        tc.logger.error("mounting volume %s failed" % volname)
        rc = False
    if rc:
        ret, _, _ = tc.run(tc.clients[0], "cp -r /etc %s" % mountpoint)
        if ret != 0:
            tc.logger.error("cp failed on the mountpoint")
            rc = False
        tc.run(tc.clients[0], "umount %s || umount -l %s" % (mountpoint, mountpoint))
    tc.run(mnode, "gluster --mode=script volume stop %s" % volname)
    tc.run(mnode, "gluster --mode=script volume delete %s" % volname)
    return rc
