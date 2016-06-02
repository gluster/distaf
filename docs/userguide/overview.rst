DiSTAF - Di'stributed Systems Test Automation Framework
-------------------------------------------------------

DiSTAF is a test automation framework for distributed systems.
And it used for test automation of glusterfs and its related projects.
And this framework is written with modularity in mind. So many parts of it can
be modified for the liking of the project, without affecting other parts.
DiSTAF can be used to test projects which runs on physical machines, virtual
machines or even containers. DiSTAF  requires remote machines (or containers)
to be reachable by IP address (or FQDN). And On Linux systems it requires sshd
to be running in the remote systems with bash environment as well.


About the name
==============
DiSTAF (or distaf) is short for Di'stributed Systems Test Automation Framework.
Also distaff is a tool used in spinning, which is designed to hold unspun 
fibres together keeping them untangled and thus easing the process of spinning.
This framework is trying to do just that, keeping the machines untangled and
easing the process of writing and executing the test cases.
Hence the name DiSTAF (distaf).

Architecture of the Framework
=============================

Terminologies used:
	*Management node*
		The node from which this test suite is executed.
		This node is responsible for orchestration of test automation.
	*Test machines*
		These include all the systems that participate in the tests.
		This can be physical machines, VMs or containers.

.. figure::  ../images/distaf_acrhitecture.jpg
   :align: center
   :width: 1200

   Architecture of DiSTAF

To run distaf, passwordless ssh should be setup from *management node* to all
the *test machines*. The *management node* connects to *test machines* using
rpyc zero-deploy, which internally makes use of ssh tunneling protocol for
establishing and maintaining the secure connections. The connection is kept
open for the entire duration of the tests. All the synchronous commands run by
the test cases, uses this connection to run them. For asynchronous calls, a
new connection is opened. This connection will be closed when async command returns.

DiSTAF uses `python-unittest` for running tests and generating the results.

When a test run is started, DiSTAF first reads a *config file*, which is in yaml format.
The *config file* will have information about servers and clients DiSTAF can connect to.
DiSTAF establishes a ssh connection to each of the servers and clients,
and maintains the connection until the end of the test run.
All the remote commands, bash or python will go through this connection.
Since most gluster automation tests require a bash commands,
DiSTAF provides two APIs to run them synchronously and asynchronously.
For more information about distaf APIs, please refer HOWTO.

Test case philosophy
====================

DiSTAF has two modes of running. The **Global Mode** and **Non-global Mode**.
There is a configuration variable in config.yml **global_mode** to toggle between them.
The idea here is that each test case should be independent of the volume type and access protocol used to mount the volume.

When the distaf is started in the *non-global mode*,
it runs each test case against all the volume type and mount protocol combinations.
This means a single test case will run many times and each time a different volume and mount combination is used.
Each test case will have it's own metadata in yaml format in test case docstring.
For more information about the fields and values of test case metadata (test case config), please refer to HOWTO.

When distaf is started in *global mode*, each test case is run only once.
The volume type and mount protocol specified in the config.yml is used for each test case.
This is helpful if a test case needs to run against a particular type of volume, to run some checks.

Few things to take care before running test case in DiSTAF
==========================================================
* Setting up and provisioning the test machines. This needs to be handled before running distaf tests.
* Updating the config.yml and setting up password-less ssh from management node to test machines.
* Installing the glusterfs and related packages is test machines.
* Creating xfs bricks in the gluster servers to serve as bricks. There are plans to handle this using [gdeploy] (https://github.com/gluster/gdeploy). But as of now, nothing is in place and bricks needs to be created in the remote test machines. And distaf expects this to be mounted at /bricks/bricks{0..n}. This will be made more configurable in future.
* Keeping the test machines in the same state if a test case fails. Since distaf does not manage the bringing up and maintaining the test machine, this should be handled outside distaf as well.
