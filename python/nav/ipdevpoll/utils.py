# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Utility functions for ipdevpoll."""

import logging

from IPy import IP

from twisted.internet import defer
from twisted.internet.defer import Deferred
from twisted.internet import reactor

from nav.oids import get_enterprise_id

_logger = logging.getLogger(__name__)

def fire_eventually(result):
    """This returns a Deferred which will fire in a later reactor turn.

    Can be used to cause a break in deferred chain, so the number of
    stack frames won't exceed sys.getrecursionlimit().  Do like this:

    >>> deferred_chain.addCallback(lambda thing: fire_eventually(thing))

    Reference:
    http://twistedmatrix.com/pipermail/twisted-python/2008-November/018693.html

    """
    deferred = Deferred()
    reactor.callLater(0, deferred.callback, result)
    return deferred

def binary_mac_to_hex(binary_mac):
    """Converts a binary string MAC address to hex string.

    If the binary string exceeds 6 octets, only the last 6 octets are
    converted. If the string contains less than 6 octets the result will be
    padded with leading zeros.

    """
    MAX_LENGTH = 6
    if binary_mac:
        binary_mac = binary_mac[-6:].rjust(MAX_LENGTH, '\x00')
        return ":".join("%02x" % ord(x) for x in binary_mac)

def truncate_mac(mac):
    """Takes a MAC address on the form xx:xx:xx... of any length and returns
    the first 6 parts.
    """
    parts = mac.split(':')
    if len(parts) > 6:
        mac = ':'.join(parts[:6])
    return mac

def find_prefix(ip, prefix_list):
    """Takes an IPy.IP object and a list of manage.Prefix and returns the most
    precise prefix the IP matches.
    """
    ret = None
    for p in prefix_list:
        sub = IP(p.net_address)
        if ip in sub:
            # Return the most precise prefix, ie the longest prefix
            if not ret or IP(ret.net_address).prefixlen() < sub.prefixlen():
                ret = p
    return ret

def is_invalid_utf8(string):
    """Returns True if string is invalid UTF-8.

    If string is not a an str object, or is decodeable as UTF-8, False is
    returned.

    """
    if isinstance(string, str):
        try:
            string.decode('utf-8')
        except UnicodeDecodeError, e:
            return True
    return False


def log_unhandled_failure(logger, failure, msg, *args, **kwargs):
    """Logs a Failure with traceback using logger.

    If the logger has an effective loglevel of debug, a verbose traceback
    (complete with stack frames) is logged.  Otherwise, a regular traceback is
    loggged.

    """
    detail = 'default'
    if logger.getEffectiveLevel() <= logging.DEBUG:
        detail = 'verbose'
    traceback = failure.getTraceback(detail=detail)
    args = args + (traceback,)

    logger.error(msg + "\n%s", *args, **kwargs)

@defer.inlineCallbacks
def get_multibridgemib(agentproxy):
    """Returns a MultiBridgeMib retriever pre-populated with instances from
    get_dot1d_instances()

    """
    from nav.mibs.bridge_mib import MultiBridgeMib
    instances = yield get_dot1d_instances(agentproxy)
    defer.returnValue(MultiBridgeMib(agentproxy, instances))

@defer.inlineCallbacks
def get_dot1d_instances(agentproxy):
    """Gets a list of alternative BRIDGE-MIB instances from a Cisco agent.

    First

    :returns: A list of [(description, community), ...] for each alternate
              BRIDGE-MIB instance.

    """
    from nav.mibs.snmpv2_mib import Snmpv2Mib
    from nav.mibs.cisco_vtp_mib import CiscoVTPMib
    from nav.mibs.entity_mib import EntityMib

    cisco = 9
    enterprise_id = yield (Snmpv2Mib(agentproxy).get_sysObjectID().
                           addCallback(get_enterprise_id))
    if enterprise_id == cisco:
        for mibclass in (EntityMib, CiscoVTPMib):
            mib = mibclass(agentproxy)
            instances = yield mib.retrieve_alternate_bridge_mibs()
            if instances:
                defer.returnValue(instances)
    defer.returnValue([])

