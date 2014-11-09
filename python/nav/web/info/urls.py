#
# Copyright (C) 2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Django URL configuration"""

from django.conf.urls.defaults import patterns, include, url
from nav.web.info.views import index, osm_map_redirecter

urlpatterns = patterns('',
    url(r'^$', index, name="info-search"),
    url(r'^osm_map_redirect/$', osm_map_redirecter,
        name='base_osm_map_redirect'),
    url(r'^osm_map_redirect/(.+)/(.+)/(.+)\.png', osm_map_redirecter,
        name='osm_map_redirect'),
    url(r'^room/', include('nav.web.info.room.urls')),
    url(r'^vlan/', include('nav.web.info.vlan.urls')),
    url(r'^devicegroup/', include('nav.web.info.netboxgroup.urls')),
)
