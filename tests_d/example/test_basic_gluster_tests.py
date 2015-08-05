from libs.util import tc, testcase
from libs.mount_ops import mount_volume, umount_volume
from libs.volume_ops import setup_vol, stop_volume, delete_volume

@testcase("gluster_basic_test")
def gluster_basic_test():
    tc.logger.info("Testing gluster volume create and mounting")
    volname = tc.config_data['VOLNAME']
    mount_type = tc.config_data['MOUNT_TYPE']
    mountpoint = tc.config_data['MOUNTPOINT']
    mnode = tc.nodes[0]
    client = tc.clients[0]
    _rc = True
    ret = setup_vol()
    if not ret:
        tc.logger.error("Unable to setup the volume %s" % volname)
        return False
    tc.run(mnode, "gluster volume status %s" % volname)
    ret, _, _ = mount_volume(volname, mount_type, mountpoint, mclient=client)
    if ret != 0:
        tc.logger.error("mounting volume %s failed" % volname)
        _rc = False
    else:
        ret, _, _ = tc.run(client, "cp -r /etc %s" % mountpoint)
        if ret != 0:
            tc.logger.error("cp failed on the mountpoint")
            _rc = False
    umount_volume(client, mountpoint)
    ret = stop_volume(volname)
    if not ret:
        _rc = False
    ret = delete_volume(volname)
    if not ret:
        _rc = False
    return _rc
