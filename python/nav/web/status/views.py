#
# Copyright (C) 2009-2011 UNINETT AS
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
"""Views for status tool"""

from datetime import datetime
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404, redirect

from nav.django.utils import get_account
from nav.django.decorators import require_admin
from nav.models.profiles import StatusPreference
from nav.models.manage import Organization, Category
from nav.models.fields import INFINITY
from nav.models.event import AlertHistory
from nav.web.message import Messages, new_message

from nav.web.status.sections import get_user_sections, get_section_model
from nav.web.status.forms import AddSectionForm
from nav.web.status.utils import extract_post, order_status_preferences
from nav.web.status.utils import make_default_preferences

SERVICE_SECTIONS = (
    StatusPreference.SECTION_SERVICE,
    StatusPreference.SECTION_SERVICE_MAINTENANCE
)


def status(request):
    """Main status view."""
    account = get_account(request)
    sections = get_user_sections(account)

    if not sections:
        make_default_preferences(account)
        sections = get_user_sections(account)

    return render_to_response(
        'status/status.html',
        {
            'active': {'status': True},
            'sections': sections,
            'title': 'NAV - Status',
            'navpath': [('Home', '/'), ('Status', '')],
        },
        RequestContext(request)
    )


def preferences(request):
    """Allows user customization of the status page."""
    if request.method == 'POST':
        request.POST = extract_post(request.POST.copy())
        if request.POST.get('moveup') or request.POST.get('movedown'):
            return move_section(request)
        elif request.POST.get('delete'):
            return delete_section(request)

    account = get_account(request)
    sections = StatusPreference.objects.filter(account=account)

    return render_to_response(
        'status/preferences.html',
        {
            'active': {'preferences': True},
            'sections': sections,
            'add_section_form': AddSectionForm(),
            'title': 'Nav - Status preferences',
            'navpath': [('Home', '/'), ('Status', '')],
        },
        RequestContext(request)
    )


def edit_preferences(request, section_id):
    """Controller for editing preferences"""
    if request.method == 'POST':
        return save_preferences(request)

    account = get_account(request)
    status_prefs = get_object_or_404(StatusPreference, id=section_id,
                                     account=account)

    section_model = get_section_model(status_prefs.type)
    form = section_model.form(status_prefs)

    return render_to_response(
        'status/edit_preferences.html',
        {
            'active': {'preferences': True},
            'name': status_prefs.name,
            'type': status_prefs.readable_type(),
            'section_form': form,
            'title': 'NAV - Edit status preference section',
            'navpath': [('Home', '/'), ('Status', '')],
        },
        RequestContext(request)
    )


def add_section(request):
    """Controller for adding a section"""
    if not request.method == 'POST':
        return HttpResponseRedirect(reverse('status-preferences'))
    elif 'save' in request.POST:
        return save_preferences(request)

    section_type = request.POST.get('section', None)
    name = StatusPreference.lookup_readable_type(section_type)
    initial = {'name': name, 'type': section_type}

    section_model = get_section_model(section_type)
    form_model = section_model.form_class()
    form = form_model(initial=initial)

    return render_to_response(
        'status/edit_preferences.html',
        {
            'active': {'preferences': True},
            'name': name,
            'section_form': form,
            'title': 'NAV - Add new status section',
            'navpath': [('Home', '/'), ('Status', '')],
        },
        RequestContext(request),
    )


def save_preferences(request):
    """Controller for saving the preferences"""
    if not request.method == 'POST':
        return HttpResponseRedirect(reverse('status-preferences'))

    account = get_account(request)

    type = request.POST.get('type', None)
    section_model = get_section_model(type)
    form_model = section_model.form_class()
    form = form_model(request.POST)

    if type and form.is_valid():
        try:
            section = StatusPreference.objects.get(id=form.cleaned_data['id'])
            type = section.type
        except StatusPreference.DoesNotExist:
            section = StatusPreference()
            section.position = StatusPreference.objects.count()
            type = form.cleaned_data['type']
            section.type = type

        section.name = form.cleaned_data['name']
        section.account = account
        if 'states' in form.cleaned_data:
            section.states = ",".join(form.cleaned_data['states'])
        if type in SERVICE_SECTIONS:
            section.services = ",".join(form.cleaned_data['services'])

        section.save()

        section.organizations = Organization.objects.filter(
            id__in=form.cleaned_data['organizations'])

        if type not in SERVICE_SECTIONS:
            section.categories = Category.objects.filter(
                id__in=form.cleaned_data['categories'])

        new_message(request, 'Saved preferences', Messages.SUCCESS)
        return HttpResponseRedirect(reverse('status-preferences'))
    else:
        if 'id' in request.POST and request.POST.get('id'):
            section = StatusPreference.objects.get(id=request.POST.get('id'))
            name = section.name
            type = section.type
        elif 'type' in request.POST and request.POST.get('type'):
            name = StatusPreference.lookup_readable_type(
                request.POST.get('type'))
            type = None

        new_message(request, 'There were errors in the form below.',
                    Messages.ERROR)
        return render_to_response(
            'status/edit_preferences.html',
            {
                'active': {'preferences': True},
                'title': 'NAV - Add new status section',
                'navpath': [('Home', '/'), ('Status', '')],
                'section_form': form,
                'name': name,
                'type': type,
            },
            RequestContext(request)
        )


def move_section(request):
    """Controller for moving a section up or down"""
    account = get_account(request)

    # Moving up, or moving down?
    if request.POST.get('moveup'):
        movement = -1
        section_id = request.POST.get('moveup')
        direction = 'up'
    elif request.POST.get('movedown'):
        movement = 1
        section_id = request.POST.get('movedown')
        direction = 'down'
    else:
        return HttpResponseRedirect(reverse('status-preferences'))

    # Make sure the ordering is correct before we try to move around
    order_status_preferences(account)

    # Find the section we want to move
    try:
        section = StatusPreference.objects.get(
            id=section_id,
            account=account,
        )
    except StatusPreference.DoesNotExist:
        new_message(request, 'Could not find selected filter', Messages.ERROR)
        return HttpResponseRedirect(reverse('status-preferences'))

    # Find the section we should swap places with.
    # If it's not found we're trying to move the first section up or the last
    # section down.
    try:
        other_section = StatusPreference.objects.get(
            position=section.position + movement,
            account=account,
        )
    except StatusPreference.DoesNotExist:
        new_message(request, 'New position is out of bounds.', Messages.ERROR)
        return HttpResponseRedirect(reverse('status-preferences'))

    # Swap places
    new_position = other_section.position
    other_section.position = section.position
    section.position = new_position

    other_section.save()
    section.save()

    new_message(request,
                'Moved section "%s" %s' % (section.name, direction),
                Messages.SUCCESS)
    return HttpResponseRedirect(reverse('status-preferences'))


def delete_section(request):
    """Controller for deleting a section"""
    if not request.method == 'POST':
        return HttpResponseRedirect(reverse('status-preferences'))

    account = get_account(request)
    section_ids = request.POST.getlist('delete_checkbox')

    sections = StatusPreference.objects.filter(
        pk__in=section_ids,
        account=account,
    ).delete()

    new_message(request, 'Deleted selected sections', Messages.SUCCESS)
    return HttpResponseRedirect(reverse('status-preferences'))


@require_admin
def resolve_alert(request):
    """Resolve an alert by settings end_time = now"""
    alertid = request.REQUEST.get('alertid')
    alert = get_object_or_404(AlertHistory, pk=alertid)
    if alert.end_time == INFINITY:
        alert.end_time = datetime.now()
        alert.save()
        if request.is_ajax():
            return HttpResponse()
        else:
            return redirect('status-index')

    return HttpResponse(status=400)
