glusterfs test automation framework
==============================================

This is a glusterfs test automation framework written in python. The framework
is written with portability in mind. It just needs ip addresses or resolvable
hostnames of servers and clients. The servers and clients can be physical machines
of vms or even linux conatiners.

Architecture of the Framework
==============================
An rpc server (server_rpycd) runs as a daemon on each of the nodes in the test
cluster and listens in a particular port. The management node (The node from which
this test suite is executed) connects to each nodes in the test cluster.

The connection to each node is done at the start of tests and each test case uses
this connection to execute any commands in the servers/clients. The connection is
tear down at the end of tests. Any disconnection for any reason will trigger a
reconnection from the management node.


How to run
=============

1. Clone this git repo and cd in to it i.e. `cd glusterfs-automation-framework`

2. scp libs/server_rpycd /usr/local/bin to each of your server nodes.

3. scp libs/rcscript_server_rpycd to /etc/init.d/server_rpycd to all
   of your servers/nodes.

4. Start the server using /etc/init.d/server_rpycd start

5. Run the following commands in each of your machines.
   chkconfig server_rpycd --add
   chkconfig server_rpycd on

6. Source the config.sh file which has information about test environment.

7. Now run main.py with proper options
 - To run only test case: `python main.py -t 123456`

   - To run bunch of test cases: `python main.py -t "12345 06783"`

   - To run all tests in a directory: `python main.py -d snapshot`

How to write tests
====================

1. Create a directory inside ./tests_d with your component name.
   The name should qualify to be a python variable which can be importable
   from other modules.

2. Write a testcase using the test_*.py

3. For test skeleton and example please look at the
   tests_d/example/test_basic_gluster_tests.py

TODO
=====

* Automating the initial setup part using pexpect or expect
* Better test case selection logic
* Better logging of test cases/results
* Forcing the order of execution if testcases whenever required
* Integrating with nose tests for Jenkins friendly reporting format
* Logs monitoring in each servers
* More and more library functions

Integration Work
=================

I am also spending some time on integrating this project with dockit (https://github.com/humblec/dockit)
This would enable to simulate multinode testing from single host node. Each of the servers and clients
would be docker containers.
