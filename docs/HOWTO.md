# DiSTAF

DiSTAF (or distaf) is a test framework for distributed systems like glusterfs. This file contains information about how to write test cases in distaf framework and how to execute them once they are written. For information about overview and architecture, please refer to [README.md](https://github.com/gluster/distaf/blob/master/README.md).

## Little about the APIs

DiSTAF exposes few APIs to interact and control the remote test machines. That is the core part of distaf. And since most test steps of glusterfs are bash/shell commands (at least on the server side), distaf exposes two APIs to run the bash/shell commands remotely. These APIs are actually methods of connection manager object and will be accessible through the object `tc`

```python
(ret, stdout, stderr) = tc.run(node, command, user='root', verbose=True)
```

So the `run` method execute the bash `command` in remote `node` as user `root` synchronously and returns a python tuple of return code, output in stdout and output in stderr.

The asynchronous version of `run` method returns a `popen` object which is very similar to `subprocess.Popen`. The object has methods to wait, communicate and get the return code etc. It has has another method `value()` to get the tuple of `(ret, stdout, stderr)`

```python
popen = tc.run_async(node, command, user='root', verbose=True)
popen.wait()
(ret, stdout, stderr) = popen.value()
```

These are most used APIs for distaf. You can also request for a connection and run python command on the remote machines. The below example should make things bit more clear.

```python
conn = tc.get_connection(node, user='root')
if conn == -1:
    tc.logger.error("Unable to establish connection to %s@%s", node, user)
    return False
# Remote python modules are accessible through conn.modules.<module_name>
pwd = conn.modules.os.getcwd()
conn.modules.os.chdir("/tmp") # Stateful. Remains in /tmp
pwd = conn.modules.os.getcwd()
r_hostname = conn.modules.socket.gethostname()
```

For more info about all the APIs, please refer "DiSTAF API Guide"

## Writing Tests in DiSTAF
#### Things to mind before writing the tests
* DiSTAF expects that the file in which test cases are written starts with `test_`. For example `test_basic_gluster.py`.
* And each test case file needs to import connection manager object to interact with the remote test nodes.
* Each of the test case should have a decorator `@testcase` with the test case name.
* Each test case should have its metadata, namely the volume type it can run on, the possible mount protocols with which it can be run and if fresh setup is required to run that test. The next section will explain a bit more about these metadata.
* A test case can be a class or a simple function.
    * If test case is a function, it is considered standalone. That is, the test case should take care of starting glusterd, creating volume, cleaning up the volume after the test etc. The framework itself will not be doing anything to assist the test case function.
    * If the test case is a class it should have at least three methods.
        1. `setup` - To setup part of test case. Like volume create maybe.
        2. `run` - This contains the test case steps. This part does all the validations and verifications.
        3. `teardown` - This part contains the tearing down the setup that was done in `setup`
    
      There is one more method `cleanup`, which is hidden. This method does the hard cleanup of gluster environment. Test case writers are not advised to use this method unless its really required. This method is called internally by DiSTAF when needed.

As you can see, there are obvious advantages of having test case as python class. So to further make the test case writing easier, a base class is written for gluster tests which does implement `setup` and `teardown` methods. This base class is called `GlusterBaseClass`. So all test cases should use this class as base class which creates a volume for the test case, depending on the values in configuration file. So test case class has to just implement the `run` method which has test case steps, assuming the volume is already created. Read more about these methods in the next section.

Example skeleton of a test case in DiSTAF.
```python
from distaf.util import tc, testcase

@testcase("testcase_skeleton")
class skeleton_gluster_test(GlusterBaseClass):
    """
    runs_on_volume: [ distribute, replicate ]
    runs_on_protocol: [ glusterfs, nfs ]
    resuse_setup: True
    summary: This is just a skeleton of a gluster test class in distaf
    # The setup and teardown are already implemented in GlusterBaseClass
    """
    def run(self):
        tc.logger.info("The volume name is %s", self.volname)
        pass # Test case steps here
        return True
```

#### About the test case metadata
Each test case has three or four metadata about the test case. These fields explain on what conditions, the test case can be run.

* `runs_on_volume: ALL` - This explains on what all volume types this test case can be run. The possible values are "distribute, replicate, dist_rep, disperse, dist_disperse". As of now DiSTAF only does string comparison, so the value should match. Alternatively you can mention ALL, which will be expanded to all possible volume types. The tiered volume type will be added soon.
* `runs_on_protocol: glusterfs` - The possible mount protocols which can be used to run this test case with. The possible values are glusterfs and nfs. The samba and cifs will be added soon.
* `reuse_setup: True` - If your test case requires a fresh setup of volume (e.g glusterfind), this should be set to False. If your testcase can reuse the existing setup, please set it to True.

We plan to have few more metadata soon. Like `testcase_tags` and `runs_on_server_version` etc.


#### About the methods of test case class
As explained in above section, each test class should have at least `run` method implemented. The `setup` and `teardown` can be used from the base class.

##### The `setup` method:
This method is responsible for creating the volumes (if it doesn't exist already). Only override this class with your own implementation if you don't need to create volume as part of setup. Or have some requirement to not to do so. Note that volume will not be mounted as part of this method and has to be taken care in `run` method. Also this method takes care of cleaning up the previous volume and re-creating it if `reuse_setup=False`. So if you override this method, please consider it as well.
##### The `run` method:
Each test case class is supposed to implement this. This should contain the actual test case steps and should do all validations and verifications needed for the test case. This is not implemented in the base class, so this must be implemented in the test case class.
##### The `teardown` method:
If should tear down any specific things you do in `run` method. Like unmounting the volume, removing the files maybe etc.
##### The `cleanup` method:
This is more of a internal method used to hard cleanup while jumping from one volume type to next volume. And this will be called only if the volume type changes from one test case to next test case.

Now you can start writing your test case (`run` method to be more specific). DiSTAF also has lot of gluster related library function to assist in test case writing. For more information please refer to API guide.

## Installing DiSTAF package
Please note that, to install this package you need to have python-setuptools, git(Most likely will be available through yum/apt-get) and python modules like rpyc, pyyaml (will be available through pip) and should be run with root privileges.
```bash
yum install python-setuptools
easy_install pip
yum install git
pip install rpyc
pip install pyyaml
```
The distaf core package can be installed through below command. It will install the distaf core package from the git HEAD available from distaf.git.
```bash

pip install git+https://github.com/gluster/distaf@master
```
If you have cloned the distaf.git, please follow the below steps to install distaf package
```
cd <distaf.git>
python setup.py install
```

## Running the tests written in DiSTAF
Before running the distaf tests, please read the [README](https://github.com/gluster/distaf/blob/master/README.md). So before running, you should have a server with glusterfs installed and a client (if your test case require it).

#### Updating the config.yml file
DiSTAF reads the run time configuration parameters from the yaml config file. Please [take a look at the sample config file](https://github.com/gluster/distaf/blob/master/config.yml). Most of the fields explain themselves.
* The `remote_user` field is the user with which distaf connects to remote test machines. It is to this user you should setup password-less ssh to.
* All server related details will go to servers field. It has subsection host and devices.
* All client related details  will go to clients field.
* You can have fields for volume types and its configurations.
* When global_mode=True, all test cases will be run against the volume type and configuration which is mentioned in the config yaml file and ignores 'runs_on_volume' and 'runs_on_protocol' in testcase metadata. If global_mode=False, each test case will run against all possible types of volume and mount protocol which is mentioned in the testcase metadata.

#### Starting the DiSTAF run
There are few ways to run the distaf test cases.

###### Running all the tests in a directory
```bash
distaf -c <path_to_config_yaml_file> -d "dir_name"
```
Note that distaf tries to recursively find all the tests inside. This is helpful when all the tests of a component are together in a directory and you want to run them all.
###### Running all the tests in a file
```bash
distaf -c <path_to_config_yaml_file> -f <path_to_file>
```
Make sure that is the file where test case class is implemented.
###### Running only the tests specified
```bash
distaf -c <path_to_config_yaml_file> -d "dir_to_look" -t "test0 test1 test2"
```
Only the tests specified from that directory is executed. If the test case is not found, it is skipped and other test cases which are found are executed.
###### Get the result in junit style
```bash
distaf -c <path_to_config_yaml_file> "test_dir" -t "Test0 Test1 Test2" -j "result_dir"
```
All DiSTAF results are by default text format and thrown to the console. If you rather use Jenkins friendly junit style xml output, you should pass `-j` with a dir where results will be populated.
###### Running all the tests in a directory with multiple config files
```bash
distaf -c "<path_to_config_yaml_file1> <path_to_config_yaml_file2>" -d "dir_name"
```

