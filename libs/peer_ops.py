from libs.util import tc


def peer_probe(pnode='', servers=''):
    """
        Does peer probe and validates the same

        Returns True on success and False of failure
    """
    global tc
    if pnode == '':
        pnode = tc.nodes[0]
    if servers == '':
        servers = tc.nodes[1:]
    rc = True
    for peer in servers:
        ret = tc.run(pnode, "gluster peer probe %s" % peer)
        if ret[0] != 0:
            tc.logger.error("peer probe to machine %s failed" % peer)
            rc = False
    return rc
