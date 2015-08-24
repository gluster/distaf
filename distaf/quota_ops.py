from distaf.util import tc


def enable_quota(volname, server=''):
    """
        Enables quota on the specified volume

        Returns the output of quota cli command
    """
    if server == '':
        server = tc.nodes[0]
    cmd = "gluster volume quota %s enable" % volname
    return tc.run(server, cmd)


def set_quota_limit(volname, path='/', limit='100GB', server=''):
    """
        Sets limit-usage on the path of the specified volume to
        specified limit

        Returs the output of quota limit-usage command
    """
    if server == '':
        server = tc.nodes[0]
    cmd = "gluster volume quota %s limit-usage %s %s" % (volname, path, limit)
    return tc.run(server, cmd)
