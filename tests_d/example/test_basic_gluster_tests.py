from distaf.util import tc, testcase
from distaf.distaf_base_class import DistafTestClass
from distaf.mount_ops import mount_volume, umount_volume
from distaf.volume_ops import setup_vol, stop_volume, delete_volume


@testcase("gluster_basic_test")
class gluster_basic_test(DistafTestClass):
    """
        runs_on_volumes: [ distribute, replicate, dist_rep ]
        runs_on_protocol: [ glusterfs, nfs ]
        reuse_setup: True
    """
    def run(self):
        _rc = True
        client = self.clients[0]
        tc.run(self.mnode, "gluster volume status %s" % self.volname)
        ret, _, _ = mount_volume(self.volname, self.mount_proto, \
                self.mountpoint, mclient=client)
        if ret != 0:
            tc.logger.error("Unable to mount the volume %s in %s" \
                    "Please check the logs" % (self.volname, client))
            return False
        ret, _, _ = tc.run(client, "cp -r /etc %s" % self.mountpoint)
        if ret != 0:
            tc.logger.error("cp failed in %s. Please check the logs" % client)
            _rc = False
        tc.run(client, "rm -rf %s/etc" % self.mountpoint)
        umount_volume(client, self.mountpoint)
        return _rc
