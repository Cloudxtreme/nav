# Copyright (C) 2010, 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

import os.path

from nav import db
from nav.report.generator import ReportList, Generator
from nav.buildconf import sysconfdir
from django.http import QueryDict

'''
Test report generators for basic errors.

These tests simply enumerate all known reports and ensure that the dbresult is
error free. This only ensures that the SQL can be run, no further verification
is performed.
'''


config_file = os.path.join(sysconfdir, 'report', 'report.conf')
config_file_local = os.path.join(sysconfdir, 'report', 'report.local.conf')

def test_report_generator():
    report_list = ReportList(config_file)
    for report in report_list.reports:
        report_name = report[0]
        yield report_name, check_report, report_name

def check_report(report_name):
    #uri = 'http://example.com/report/%s/' % report_name
    uri = QueryDict('').copy()
    db.closeConnections() # Ensure clean connection for each test

    generator = Generator()
    report, contents, neg, operator, adv, config, dbresult = generator.make_report(
        report_name, config_file, config_file_local, uri, None, None)

    assert dbresult, 'dbresult is None'
    assert not dbresult.error, dbresult.error + '\n' + dbresult.sql
