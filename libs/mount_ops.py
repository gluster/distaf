from libs.util import tc


def mount_volume(volname, mtype='glusterfs', mpoint='/mnt/glusterfs', \
        mserver='', mclient='', options=''):
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
            % (volname, mpoint, mserver), verbose=False)
    if ret == 0:
        tc.logger.debug("Volume %s is already mounted at %s" \
        % (volname, mpoint))
        return (0, '', '')
    mcmd = "mount -t %s %s %s:%s %s" % \
            (mtype, options, mserver, volname, mpoint)
    tc.run(mclient, "test -d %s || mkdir -p %s" % (mpoint, mpoint), \
            verbose=False)
    return tc.run(mclient, mcmd)

def umount_volume(client, mountpoint):
    """
        unmounts the mountpoint
        Returns the output of umount command
    """
    cmd = "umount %s || umount -f %s || umount -l %s" \
            % (mountpoint, mountpoint, mountpoint)
    return tc.run(client, cmd)
