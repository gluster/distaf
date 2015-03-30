from libs.util import tc

"""
    This file contains the glusterd and other initial gluster
    options like start/stop glusterd and env_setup_servers for
    initial back-end brick preperation
"""


def start_glusterd(servers=''):
    """
        Starts glusterd in all servers if they are not running

        Returns True if glusterd started in all servers
        Returns False if glusterd failed to start in any server

        (Will be enhanced to support systemd in future)
    """
    if servers == '':
        servers = tc.servers
    ret, _ = tc.run_servers("pgrep glusterd || service glusterd start", \
            servers=servers)
    return ret


def stop_glusterd(servers=''):
    """
        Stops the glusterd in specified machine(s)

        Returns True if glusterd is stopped in all nodes
        Returns False on failure
    """
    if servers == '':
        servers = tc.servers
    ret, _ = tc.run_servers("service glusterd stop", servers=servers)
    return ret


#TODO: THIS IS NOT IMPLEMENTED YET. PLEASE DO THIS MANUALLY
#      TILL WE IMPLEMENT THIS PART

def env_setup_servers(snap=True, servers=''):
    """
        Sets up the env for all the tests
        Install all the gluster bits and it's dependencies
        Installs the xfs bits and then formats the backend fs for gluster use

        Returns 0 on success and non-zero upon failing
    """
    tc.logger.info("The function isn't implemented yet")
    tc.logger.info("Please setup the bricks manually.")
    return True
