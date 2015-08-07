import os
import time
import logging
from plumbum import SshMachine
from distaf.config_parser import get_config_data
from rpyc.utils.zerodeploy import DeployedServer


class big_bang:
    def __init__(self):
        """
            Initialises the whole environment and establishes connection
        """
        self.config_data = get_config_data()

        self.nodes = self.config_data['NODES']
        self.peers = self.config_data['PEERS']
        self.clients = self.config_data['CLIENTS']
        self.gm_nodes = self.config_data['GM_NODES']
        self.gm_peers = self.config_data['GM_PEERS']
        self.gs_nodes = self.config_data['GS_NODES']
        self.gs_peers = self.config_data['GS_PEERS']
        self.number_nodes = len(self.nodes)
        self.number_peers = len(self.peers)
        self.number_clients = len(self.clients)
        self.number_gm_nodes = len(self.gm_nodes)
        self.number_gm_peers = len(self.gm_peers)
        self.number_gs_nodes = len(self.gs_nodes)
        self.number_gs_peers = len(self.gs_peers)
        self.global_flag = {}

        self.servers = self.nodes + self.peers + self.gm_nodes + \
                self.gm_peers + self.gs_nodes + self.gs_peers
        self.all_nodes = self.nodes + self.peers + self.clients + \
                self.gm_nodes + self.gm_peers + self.gs_nodes + self.gs_peers

        client_logfile = self.config_data['LOG_FILE']
        loglevel = getattr(logging, self.config_data['LOG_LEVEL'].upper())
        client_logdir = os.path.dirname(client_logfile)
        if not os.path.exists(client_logdir):
            os.makedirs(client_logdir)
        self.logger = logging.getLogger('client_rpyc')
        self.lhndlr = logging.FileHandler(client_logfile)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s '
                                     '%(message)s')
        self.lhndlr.setFormatter(formatter)
        self.logger.addHandler(self.lhndlr)
        self.logger.setLevel(loglevel)

        self.user = self.config_data['REMOTE_USER']

        self.connection_handles = {}
        self.subp_conn = {}
        for node in self.all_nodes:
            self.connection_handles[node] = {}
            self.subp_conn[node] = {}
            self.logger.debug("Connecting to node: %s" % node)
            ret = self.establish_connection(node, self.user)
            if not ret:
                self.logger.warning("Unable to establish connection with: %s" \
                        % node)
            else:
                self.logger.debug("Connected to node: %s" % node)

    def establish_connection(self, node, user):
        """
            Establishes connection from localhost to node via SshMachine and
            zerodeploy. The connection is authenticated and hence secure.
            Populates the connection in a dict called connection_handles.
            This function does not take care of timeouts. Timeouts need to
            be handled by the calling function
            Returns True on success and False otherwise
        """
        try:
            rem = SshMachine(node, user)
            dep = DeployedServer(rem)
            conn = dep.classic_connect()
            self.connection_handles[node][user] = (rem, dep, conn)
            self.subp_conn[node][user] = conn.modules.subprocess
        except:
            return False
        return True

    def refresh_connection(self, node, user='', timeout=210):
        """
            Refresh the connection to the user@node

            This should be called either from test script, but internally
            run/run_async will also call this if connection is found to be
            disconnected. Any reboot will make the connection go bad.
        """
        if user == '':
            user = self.user
        try:
            self.connection_handles[node][user][2].close()
            self.connection_handles[node][user][1].close()
            self.connection_handles[node][user][0].close()
        except:
            pass
        while timeout >= 0:
            try:
                self.establish_connection(node, user)
                break
            except:
                self.logger.debug("Couldn't connect to %s. Retrying in 42 "
                                  "seconds" % node)
                time.sleep(42)
                timeout = timeout - 42
        if timeout < 0:
            self.logger.critical("Unable to connect to %s" % node)
            return False
        else:
            self.logger.debug("Connection re-established to %s" % node)
            return True

    def run(self, node, cmd, user='', verbose=True):
        """
            Run the specified command in specified remote machine

            Returns a tuple of (retcode, stdout, stderr) of the command
            in remote machine
        """
        if user == '':
            user = self.user
        self.logger.info("Executing %s on %s" % (cmd, node))
        try:
            subp = self.subp_conn[node][user]
            p = subp.Popen(cmd, shell=True, stdout=subp.PIPE, stderr=subp.PIPE)
        except:
            ret = self.refresh_connection(node, user)
            if not ret:
                self.logger.critical("Unable to connect to %s@%s" \
                        % (user, node))
                return (-1, -1, -1)
            subp = self.subp_conn[node][user]
            p = subp.Popen(cmd, shell=True, stdout=subp.PIPE, stderr=subp.PIPE)
        pout, perr = p.communicate()
        ret = p.returncode
        self.logger.info("\"%s\" on %s: RETCODE is %d" % (cmd, node, ret))
        if pout != "" and verbose:
            self.logger.info("\"%s\" on %s: STDOUT is \n %s" % \
                            (cmd, node, pout))
        if perr != "" and verbose:
            self.logger.error("\"%s\" on %s: STDERR is \n %s" % \
                            (cmd, node, perr))
        return (ret, pout, perr)

    def run_async(self, node, cmd, user='', verbose=True):
        """
            Run the specified command in specified remote node asynchronously
        """
        if user == '':
            user = self.user
        try:
            c = self.connection_handles[node][user][1].classic_connect()
        except:
            ret = self.refresh_connection(node, user)
            if not ret:
                self.logger.critical("Couldn't connect to %s" % node)
                return None
            c = self.connection_handles[node][user][1].classic_connect()
        self.logger.info("Executing %s on %s asynchronously" % (cmd, node))
        p = c.modules.subprocess.Popen(cmd, shell=True, \
            stdout=c.modules.subprocess.PIPE, stderr=c.modules.subprocess.PIPE)

        def value():
            pout, perr = p.communicate()
            retc = p.returncode
            c.close()
            self.logger.info("\"%s\" on \"%s\": RETCODE is %d" % \
            (cmd, node, retc))
            if pout != "" and verbose:
                self.logger.debug("\"%s\" on \"%s\": STDOUT is \n %s" % \
                (cmd, node, pout))
            if perr != "" and verbose:
                self.logger.error("\"%s\" on \"%s\": STDERR is \n %s" % \
                (cmd, node, perr))
            return (retc, pout, perr)

        p.value = value
        p.close = lambda: c.close()
        return p

    def run_servers(self, command, user='', servers='', verbose=True):
        """
            Run the specified command in each of the server in parallel
        """
        if user == '':
            user = self.user
        if servers == '':
            servers = self.servers
        sdict = {}
        out_dict = {}
        ret = True
        for server in servers:
            sdict[server] = self.run_async(server, command, user, verbose)
        for server in set(servers):
            sdict[server].wait()
            ps, _, _ = sdict[server].value()
            out_dict[server] = ps
            if 0 != ps:
                ret = False
        return (ret, out_dict)

    def get_connection(self, node, user=''):
        """
            Establishes a connection to the remote node and returns
            the connection handle. Returns -1 if connection couldn't
            be established.
        """
        if user == '':
            user = self.user
        try:
            conn = self.connection_handles[node][user][1].classic_connect()
        except:
            ret = self.refresh_connection(node, user)
            if not ret:
                self.logger.critical("Couldn't connect to %s" % node)
                return -1
            conn = self.connection_handles[node][user][1].classic_connect()
        return conn

    def upload(self, node, localpath, remotepath, user=''):
        """
            Uploads the file/directory in localpath to file/directory to
            remotepath in node
            Returns None if success
            Raises an exception in case of failure
        """
        if user == '':
            user = self.user
        rem = self.connection_handles[node][user][0]
        rem.upload(localpath, remotepath)
        return None

    def add_group(self, node, group):
        """
            Adds a group in the remote node

            Returns True on success and False on failure
        """
        if 'root' not in self.connection_handles[node]:
            self.logger.error("ssh connection to 'root' of %s is not present" \
                    % node)
            return False
        conn = self.get_connection(node, 'root')
        if conn == -1:
            self.logger.error("Unable to get connection for root@%s" % node)
            return False
        try:
            conn.modules.grp.getgrnam(group)
            self.logger.debug("Group %s already exists on %s" % (group, node))
            conn.close()
            return True
        except KeyError:
            self.logger.debug("group %s does not exist in %s. Creating now" \
                    % (group, node))
            conn.close()
        ret = self.run(node, "groupadd %s" % group)
        if ret[0] != 0:
            self.logger.error("Unable to add group %s to %s" % (group, node))
            return False
        else:
            self.logger.debug("group %s added to %s" % (group, node))
            return True

    def add_user(self, node, user, password='foobar', group=''):
        """
            Add the user 'user' to the node 'node'
            For this to work, connection to 'root' account of remote machine
            should be already established.
            This functions also takes care creating a passwordless ssh
            connection from management node to remote node.
            And then it connects to remote user and updates the
            dict of connection_handles
        """
        if 'root' not in self.connection_handles[node]:
            self.logger.error("ssh connection to 'root' of %s is not present" \
                    % node)
            return False
        conn = self.get_connection(node, 'root')
        if conn == -1:
            self.logger.error("Unable to get connection to 'root' of node %s" \
                    % node)
            return False
        try:
            conn.modules.pwd.getpwnam(user)
            self.logger.debug("User %s already exist in %s" % (user, node))
            return True
        except KeyError:
            self.logger.debug("User %s doesn't exist in %s. Creating now" \
                    % (user, node))
        grp_add_cmd = ''
        if group != '':
            ret = self.add_group(node, group)
            if not ret:
                return False
            grp_add_cmd = "-g %s" % group
        else:
            group = user
            grp_add_cmd = '-U'
        ret = self.run(node, \
"useradd -m %s -p $(perl -e'print crypt(%s, \"salt\")') %s" % \
(grp_add_cmd, password, user), user='root')
        if ret[0] != 0:
            self.logger.error("Unable to add the user %s to %s" % (user, node))
            return False
        conn.modules.os.makedirs("/home/%s/.ssh" % user)
        rfh = conn.builtin.open("/home/%s/.ssh/authorized_keys" % user, "a")
        localhome = os.path.expanduser('~')
        try:
            with open("%s/.ssh/id_rsa.pub" % localhome, 'r') as f:
                for line in f:
                    rfh.write(line)
            ruid = conn.modules.pwd.getpwnam(user).pw_uid
            rgid = conn.modules.grp.getgrnam(group).gr_gid
            conn.modules.os.chown("/home/%s/.ssh/authorized_keys" % \
                    user, ruid, rgid)
        except:
            self.logger.error("Unable to write the rsa pub file to %s@%s" \
                    % (user, node))
            return False
        rfh.close()
        conn.close()
        ret = self.establish_connection(node, user)
        if not ret:
            self.logger.critical("Unable to connect to %s@%s" % (user, node))
            return False
        return True

    def fini(self):
        """
            Destroy all stored connections to user@remote-machine
        """
        for node in self.connection_handles.keys():
            for user in self.connection_handles[node].keys():
                self.logger.debug("Closing all connection to %s@%s" \
                        % (user, node))
                self.connection_handles[node][user][2].close()
                self.connection_handles[node][user][1].close()
                self.connection_handles[node][user][0].close()
