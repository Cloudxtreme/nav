#
# Copyright (C) 2003,2004 Norwegian University of Science and Technology
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
"""HTTP Service Checker"""
from nav import buildconf
from nav.statemon.DNS import socktype_from_addr

from nav.statemon.event import Event
from nav.statemon.abstractChecker import AbstractChecker
from urlparse import urlsplit
import httplib
import socket


class HTTPConnection(httplib.HTTPConnection):
    """Customized HTTP protocol interface"""
    def __init__(self, timeout, host, port=80):
        httplib.HTTPConnection.__init__(self, host, port)
        self.timeout = timeout
        self.connect()

    def connect(self):
        self.sock = socket.socket(socktype_from_addr(self.host),
                                  socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))


class HttpChecker(AbstractChecker):
    """HTTP"""
    TYPENAME = "http"
    IPV6_SUPPORT = True
    DESCRIPTION = "HTTP"
    OPTARGS = (
        ('url', ''),
        ('port', ''),
        ('timeout', ''),
    )

    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, service, port=0, **kwargs)

    def execute(self):
        ip, port = self.getAddress()
        url = self.getArgs().get('url', '')
        if not url:
            url = "/"
        _protocol, vhost, path, query, _fragment = urlsplit(url)
        
        i = HTTPConnection(self.getTimeout(), ip, port or 80)
        if vhost:
            i.host = vhost

        if '?' in url:
            path = path + '?' + query
        i.putrequest('GET', path)
        i.putheader('User-Agent',
                    'NAV/servicemon; version %s' % buildconf.VERSION)
        i.endheaders()
        response = i.getresponse()
        if 200 <= response.status < 400:
            status = Event.UP
            version = response.getheader('SERVER')
            self.setVersion(version)
            info = 'OK (%s) %s' % (str(response.status), version)
        else:
            status = Event.DOWN
            info = 'ERROR (%s) %s' % (str(response.status), url)

        return status, info
