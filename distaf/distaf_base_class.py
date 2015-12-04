from distaf.util import tc
from distaf.volume_ops import setup_vol, get_volume_info
from distaf.mount_ops import umount_volume

class DistafTestClass():
    """
        This is the base class for the distaf tests

        All tests can subclass this and then write test cases
    """

    def __init__(self, config_data):
        """
            Initialise the class with the config values
        """
        if config_data['global_mode']:
            self.volname = self.config_data['volumes'].keys()[0]
            self.voltype = self.config_data['volumes'][self.volname]['voltype']
            self.nodes = self.config_data['volumes'][self.volname]['nodes']
            self.peers = self.config_data['volumes'][self.volname]['peers']
            self.clients = self.config_data['volumes'][self.volname]['clients']
            self.mount_proto = \
                    self.config_data['volumes'][self.volname]['mount_proto']
            self.mountpoint = \
                    self.config_data['volumes'][self.volname]['mountpoint']
        else:
            self.voltype = self.config_data['voltype']
            self.volname = "%s-testvol" % self.voltype
            self.nodes = self.config_data['nodes']
            self.clients = self.config_data['clients']
            self.peers = self.config_data['peers']
            self.mount_proto = 'glusterfs'
            self.mountpoint = '/mnt/glusterfs'
        self.mnode = self.nodes[0]

    def setup(self):
        """
            Function to setup the volume for testing.
        """
        volinfo = get_volume_info(server=self.nodes[0])
        if volinfo in not None and self.volname in volinfo.keys():
            tc.logger.debug("The volume %s is already present in %s" \
                    % (self.volname, self.mnode))
        else:
            dist = rep = dispd = red = stripe = trans = ''
            if self.voltype == 'distribute':
                dist = self.config_data[self.voltype]['dist_count']
                trans = self.config_data[self.voltype]['trans']
            elif self.voltype == 'replicate':
                rep = self.config_data[self.voltype]['replica']
                trans = self.config_data[self.voltype]['trans']
            elif self.voltype == 'dist_rep':
                dist = self.config_data[self.voltype]['dist_count']
                rep = self.config_data[self.voltype]['replica']
                trans = self.config_data[self.voltype]['trans']
            elif self.voltype == 'disperse':
                dispd = self.config_data[self.voltype]['disperse']
                red = self.config_data[self.voltype]['redundancy']
                trans = self.config_data[self.voltype]['trans']
            elif self.voltype == 'dist_disperse':
                dist = self.config_data[self.voltype]['dist_count']
                disp = self.config_data[self.voltype]['disperse']
                red = self.config_data[self.voltype]['redundancy']
                trans = self.config_data[self.voltype]['trans']

            ret = setup_vol(self.volname, dist, rep, dispd, red, stripe, trans, \
                    servers=self.nodes)
            if not ret:
                tc.logger.error("Unable to setup volume %s. Aborting")
                return False
            return True

    def teardown(self):
        """
            The function to clean up the setup
        """
        umount_volume(self.clients[0], self.mountpoint)
        return True
