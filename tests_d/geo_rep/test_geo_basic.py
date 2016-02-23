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


from distaf.util import testcase, tc
from tests_d.geo_rep.geo_rep_libs import geo_rep_basic_test

@testcase("changelog-test-create")
def changelog_test_create():
    tc.logger.info("changelog-%s-%s-create-on-%s-mount" % \
    (tc.config_data['DIR_STRUCT'], tc.config_data['FILE_TYPE'], \
    tc.config_data['MOUNT_TYPE']))
    ret = geo_rep_basic_test('create')
    return ret

@testcase("changelog-test-chmod")
def changelog_test_chmod():
    tc.logger.info("changelog-%s-%s-chmod-on-%s-mount" % \
    (tc.config_data['DIR_STRUCT'], tc.config_data['FILE_TYPE'], \
    tc.config_data['MOUNT_TYPE']))
    ret = geo_rep_basic_test('chmod')
    return ret

@testcase("changelog-test-chown")
def changelog_test_chown():
    tc.logger.info("changelog-%s-%s-chown-on-%s-mount" % \
    (tc.config_data['DIR_STRUCT'], tc.config_data['FILE_TYPE'], \
    tc.config_data['MOUNT_TYPE']))
    ret = geo_rep_basic_test('chown')
    return ret

@testcase("changelog-test-chgrp")
def changelog_test_chgrp():
    tc.logger.info("changelog-%s-%s-chgrp-on-%s-mount" % \
    (tc.config_data['DIR_STRUCT'], tc.config_data['FILE_TYPE'], \
    tc.config_data['MOUNT_TYPE']))
    ret = geo_rep_basic_test('chgrp')
    return ret

@testcase("changelog-test-symlink")
def changelog_test_symlink():
    tc.logger.info("changelog-%s-%s-symlink-on-%s-mount" % \
    (tc.config_data['DIR_STRUCT'], tc.config_data['FILE_TYPE'], \
    tc.config_data['MOUNT_TYPE']))
    ret = geo_rep_basic_test('symlink')
    return ret

@testcase("changelog-test-hardlink")
def changelog_test_hardlink():
    tc.logger.info("changelog-%s-%s-hardlink-on-%s-mount" % \
    (tc.config_data['DIR_STRUCT'], tc.config_data['FILE_TYPE'], \
    tc.config_data['MOUNT_TYPE']))
    ret = geo_rep_basic_test('hardlink')
    return ret

@testcase("changelog-test-truncate")
def changelog_test_truncate():
    tc.logger.info("changelog-%s-%s-truncate-on-%s-mount" % \
    (tc.config_data['DIR_STRUCT'], tc.config_data['FILE_TYPE'], \
    tc.config_data['MOUNT_TYPE']))
    ret = geo_rep_basic_test('truncate')
    return ret

@testcase("changelog-test-rename")
def changelog_test_rename():
    tc.logger.info("changelog-%s-%s-rename-on-%s-mount" % \
    (tc.config_data['DIR_STRUCT'], tc.config_data['FILE_TYPE'], \
    tc.config_data['MOUNT_TYPE']))
    ret = geo_rep_basic_test('rename')
    return ret

@testcase("changelog-test-remove")
def changelog_test_remove():
    tc.logger.info("changelog-%s-%s-remove-on-%s-mount" % \
    (tc.config_data['DIR_STRUCT'], tc.config_data['FILE_TYPE'], \
    tc.config_data['MOUNT_TYPE']))
    ret = geo_rep_basic_test('rm')
    return ret
