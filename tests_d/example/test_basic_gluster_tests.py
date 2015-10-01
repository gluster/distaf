from distaf.util import tc, testcase
from distaf.mount_ops import mount_volume, umount_volume
from distaf.volume_ops import setup_vol, stop_volume, delete_volume

@testcase("gluster_basic_test")
def gluster_basic_test():
    """
        runs_on_volumes: ALL
        run_on_protocol: [ glusterfs, nfs ]
        packages_required: samba
    """
    tc.logger.info("Testing gluster volume create and mounting")
    volname = tc.test_config['volname']
    mount_type = tc.test_config['mount_proto']
    mountpoint = tc.test_config['mountpoint']
    mnode = tc.servers[0]
    client = tc.clients[0]
    _rc = True
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
    return _rc
