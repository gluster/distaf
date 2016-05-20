#  This file is part of DiSTAF
#  Copyright (C) 2015-2016  Red Hat, Inc. <http://www.redhat.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import os
import time
import logging

from plumbum import SshMachine
from rpyc.utils.zerodeploy import DeployedServer


class BigBang():
    """
        The big bang which starts the life in distaf
    """
    def __init__(self, configs):
        """
            Initialises the whole environment and establishes connection
        """
        self.global_config = configs

        # Initialise servers and clients
        self.servers = self.global_config['servers'].keys()
        self.clients = self.global_config['clients'].keys()
        self.all_nodes = list(set(self.servers + self.clients))
        self.num_servers = len(self.servers)
        self.num_clients = len(self.clients)
        self.user = self.global_config['remote_user']
        self.global_flag = {}

        # setup logging in distaf
        client_logfile = os.path.abspath(self.global_config['log_file'])
        loglevel = getattr(logging, self.global_config['log_level'].upper())
        client_logdir = os.path.dirname(client_logfile)
        if not os.path.exists(client_logdir):
            os.makedirs(client_logdir)
        self.logger = logging.getLogger('distaf')
        self.lhndlr = logging.FileHandler(client_logfile)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s '
                                      '%(message)s')
        self.lhndlr.setFormatter(formatter)
        self.logger.addHandler(self.lhndlr)
        self.logger.setLevel(loglevel)
        self.skip_log_inject = self.global_config.get('skip_log_inject', False)

        # Determine default connection type
        # Default to ssh w/ control persist
        self.connection_engine = self.global_config.get('connection_engine',
                                                        'ssh_controlpersist')
        if self.connection_engine == "ssh_controlpersist":
            self.use_ssh = True
            self.use_controlpersist = True
        elif self.connection_engine == "ssh":
            self.use_ssh = True
            self.use_controlpersist = False
        else:
            self.use_ssh = False
            self.use_controlpersist = False

        # connection store for _get_ssh()
        if self.use_ssh:
            # using separate ssh connections at the moment
            # ssh connections are requested on-the-fly via run()
            self.sshconns = {}

        # rpyc connection handles (still needed for on-the-fly connections)
        self.connection_handles = {}
        self.subp_conn = {}
        # skipping the rpyc connections until requested to speed startup time
        # if zerodeploy delay interferes with a testcase, user can "prime" the
        #    connection by calling establish_connection in the testcase.setup
        if not self.use_ssh:
            for node in self.all_nodes:
                self.logger.debug("Connecting to node: %s" % node)
                ret = self.establish_connection(node, self.user)
                if not ret:
                    self.logger.warning("Unable to establish connection "
                                        "with: %s" % node)
                else:
                    self.logger.debug("Connected to node: %s" % node)

    def establish_connection(self, node, user):
        """
            Establishes rpyc connection from localhost to node via SshMachine
            and zerodeploy. The connection is authenticated and hence secure.
            Populates the connection in a dict called connection_handles.
            This function does not take care of timeouts. Timeouts need to
            be handled by the calling function
            Returns True on success and False otherwise
        """
        keyfile = None
        if 'ssh_keyfile' in self.global_config:
            keyfile = self.global_config['ssh_keyfile']
        try:
            self.connection_handles[node] = {}
            self.subp_conn[node] = {}
            rem = SshMachine(node, user, keyfile=keyfile)
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
            self.logger.debug("Connection (re-)established to %s" % node)
            return True

    def _get_ssh(self, node, user):
        """Setup a SshMachine connection for non-rpyc connections"""
        ssh_opts = ()
        ssh_opts += ('-T',
                     '-oPasswordAuthentication=no',
                     '-oStrictHostKeyChecking=no',
                     '-oPort=22',
                     '-oConnectTimeout=10')

        keyfile = None
        if 'ssh_keyfile' in self.global_config:
            keyfile = self.global_config['ssh_keyfile']
            ssh_opts += ('-o', 'IdentityFile=%s' % keyfile)

        if self.use_controlpersist:
            ssh_opts += ('-oControlMaster=auto',
                         '-oControlPersist=30m',
                         '-oControlPath=~/.ssh/distaf-ssh-%r@%h:%p')

        conn_name = "%s@%s" % (user, node)
        # if no existing connection, create one
        if conn_name not in self.sshconns:
            # we already have plumbum imported for rpyc, so let's use it
            ssh = SshMachine(node, user, ssh_opts=ssh_opts)
            self.sshconns[conn_name] = ssh
        else:
            ssh = self.sshconns[conn_name]

        if ssh:
            self.logger.debug("Have ssh for %s. Returning ssh." % conn_name)
            return ssh

        self.logger.error("oops. did not get ssh for %s", conn_name)
        return None

    def run(self, node, cmd, user='', verbose=True):
        """
            Run the specified command in specified remote machine

            Returns a tuple of (retcode, stdout, stderr) of the command
            in remote machine
        """
        if user == '':
            user = self.user
        self.logger.info("Executing %s on %s" % (cmd, node))

        if self.use_ssh:
            """
            Use straight ssh for all run shell command connections,
                and only create rpyc connections as needed.
            """
            ctlpersist = ''
            if self.use_controlpersist:
                ctlpersist = " (cp)"

            # output command
            self.logger.debug("%s@%s%s: %s", user, node, ctlpersist, cmd)
            # run the command
            ssh = self._get_ssh(node, user)
            p = ssh.popen(cmd)
            pout, perr = p.communicate()
            prcode = p.returncode

            # output command results
            self.logger.info("Running %s on %s@%s RETCODE: %s",
                             cmd, user, node,  prcode)
            if pout != "" and verbose:
                self.logger.info("Running %s on %s@%s STDOUT:\n%s",
                                 cmd, user, node, pout)
            if perr != "" and verbose:
                self.logger.error("Running %s on %s@%s STDERR:\n%s",
                                  cmd, user, node, perr)

            return (prcode, pout, perr)
        else:
            try:
                subp = self.subp_conn[node][user]
                p = subp.Popen(cmd, shell=True,
                               stdout=subp.PIPE, stderr=subp.PIPE)
            except:
                ret = self.refresh_connection(node, user)
                if not ret:
                    self.logger.critical("Unable to connect to %s@%s" %
                                         (user, node))
                    return (-1, -1, -1)
                subp = self.subp_conn[node][user]
                p = subp.Popen(cmd, shell=True,
                               stdout=subp.PIPE, stderr=subp.PIPE)
            pout, perr = p.communicate()
            ret = p.returncode
            self.logger.info("\"%s\" on %s: RETCODE is %d" % (cmd, node, ret))
            if pout != "" and verbose:
                self.logger.info("\"%s\" on %s: STDOUT is \n %s" %
                                 (cmd, node, pout))
            if perr != "" and verbose:
                self.logger.error("\"%s\" on %s: STDERR is \n %s" %
                                  (cmd, node, perr))
            return (ret, pout, perr)

    def run_async(self, node, cmd, user='', verbose=True):
        """
            Run the specified command in specified remote node asynchronously
        """
        if user == '':
            user = self.user

        if self.use_ssh:
            ctlpersist = ''
            if self.use_controlpersist:
                ctlpersist = " (cp)"

            # output command
            self.logger.debug("%s@%s%s: %s" % (user, node, ctlpersist, cmd))
            # run the command
            ssh = self._get_ssh(node, user)
            p = ssh.popen(cmd)

            def value():
                stdout, stderr = p.communicate(input=cmd)
                retcode = p.returncode
                # output command results
                self.logger.info("Running %s on %s@%s RETCODE: %s",
                                 cmd, user, node, retcode)
                if stdout:
                    self.logger.info("Running %s on %s@%s STDOUT...\n%s",
                                     cmd, user, node, stdout)
                if stderr:
                    self.logger.info("Running %s on %s@%s STDERR...\n%s",
                                     cmd, user, node, stderr)
                return (retcode, stdout, stderr)

            p.value = value
            return p
        else:
            try:
                c = self.connection_handles[node][user][1].classic_connect()
            except:
                ret = self.refresh_connection(node, user)
                if not ret:
                    self.logger.critical("Couldn't connect to %s" % node)
                    return None
                c = self.connection_handles[node][user][1].classic_connect()
            self.logger.info("Executing %s on %s asynchronously" % (cmd, node))
            p = c.modules.subprocess.Popen(cmd, shell=True,
                                           stdout=c.modules.subprocess.PIPE,
                                           stderr=c.modules.subprocess.PIPE)

            def value():
                """
                A function which returns the tuple of
                (retcode, stdout, stdin)
                """
                pout, perr = p.communicate()
                retc = p.returncode
                c.close()
                self.logger.info("\"%s\" on \"%s\": RETCODE is %d" %
                                 (cmd, node, retc))
                if pout != "" and verbose:
                    self.logger.debug("\"%s\" on \"%s\": STDOUT is \n %s" %
                                      (cmd, node, pout))
                if perr != "" and verbose:
                    self.logger.error("\"%s\" on \"%s\": STDERR is \n %s" %
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
        servers = list(set(servers))
        sdict = {}
        out_dict = {}
        ret = True
        for server in servers:
            sdict[server] = self.run_async(server, command, user, verbose)
        for server in servers:
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
            self.logger.error("ssh connection to 'root' of %s is not present" %
                              node)
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
            self.logger.debug("group %s does not exist in %s. Creating now" %
                              (group, node))
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
            self.logger.error("ssh connection to 'root' of %s is not present" %
                              node)
            return False
        conn = self.get_connection(node, 'root')
        if conn == -1:
            self.logger.error("Unable to get connection to 'root' of node %s" %
                              node)
            return False
        try:
            conn.modules.pwd.getpwnam(user)
            self.logger.debug("User %s already exist in %s" % (user, node))
            return True
        except KeyError:
            self.logger.debug("User %s doesn't exist in %s. Creating now" %
                              (user, node))
        grp_add_cmd = ''
        if group != '':
            ret = self.add_group(node, group)
            if not ret:
                return False
            grp_add_cmd = "-g %s" % group
        else:
            group = user
            grp_add_cmd = '-U'

        ret = self.run(node, "useradd -m %s -p $(perl -e'print "
                       "crypt(%s, \"salt\")') %s" %
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
            conn.modules.os.chown("/home/%s/.ssh/authorized_keys" %
                                  user, ruid, rgid)
        except:
            self.logger.error("Unable to write the rsa pub file to %s@%s" %
                              (user, node))
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
                self.logger.debug("Closing all connection to %s@%s" %
                                  (user, node))
                self.connection_handles[node][user][2].close()
                self.connection_handles[node][user][1].close()
                self.connection_handles[node][user][0].close()
