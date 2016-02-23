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


from distaf.util import tc, testcase
from distaf.distaf_base_class import DistafTestClass


@testcase("this_should_pass")
class get_hostname(DistafTestClass):
    """
        runs_on_volumes: ALL
        runs_on_protocol: [ glusterfs, nfs, cifs ]
        reuse_setup: True
    """
    def setup(self):
        return True

    def run(self):
        tc.logger.info("Testing connection and command exec")
        ret = 0
        ret, _, _ = tc.run(self.nodes[0], "hostname")
        if ret != 0:
            tc.logger.error("hostname command failed")
            return False
        else:
            return True

    def teardown(self):
        return True

    def cleanup(self):
        return True

@testcase("this_should_fail")
class going_to_fail(DistafTestClass):
    """
        runs_on_volumes: ALL
        runs_on_protocol: [ glusterfs, nfs ]
        reuse_setup: True
    """
    def setup(self):
        return True

    def run(self):
        tc.logger.info("Testing fail output")
        ret = 0
        ret, _, _ = tc.run(self.nodes[0], "false")
        if ret != 0:
            tc.logger.error("false command failed")
            return False
        else:
            return True

    def teardown(self):
        return True

    def cleanup(self):
        return True
