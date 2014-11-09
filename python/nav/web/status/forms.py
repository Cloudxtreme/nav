#
# Copyright (C) 2009-2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#

from itertools import chain
from django import forms
from django.utils.encoding import force_unicode

from nav.models.profiles import StatusPreference
from nav.models.manage import Netbox, Organization, Category
from nav.web import servicecheckers

from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Row, Column, Field
from nav.web.crispyforms import LabelSubmit


def _organization_choices():
    org = [(org.id, org.description) for org in Organization.objects.all()]
    return [('', '(all)')] + org


def _category_choices():
    cat = [(cat.id, cat.description) for cat in Category.objects.all()]
    return [('', '(all)')] + cat


def _service_choices():
    service = [(s, s) for s in servicecheckers.get_checkers()]
    return [('', '(all)')] + service


def _state_choices():
    return (
        (Netbox.UP_DOWN, 'down'),
        (Netbox.UP_SHADOW, 'shadow'),
    )


def _all_state_choices():
    return (
        (Netbox.UP_UP, 'up'),
        (Netbox.UP_DOWN, 'down'),
        (Netbox.UP_SHADOW, 'shadow'),
    )


class SectionForm(forms.Form):
    id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    name = forms.CharField()
    type = forms.CharField(widget=forms.HiddenInput())
    organizations = forms.MultipleChoiceField()

    def __init__(self, *args, **kwargs):
        super(SectionForm, self).__init__(*args, **kwargs)
        self.fields['organizations'].choices = _organization_choices()
        if 'categories' in self.fields:
            self.fields['categories'].choices = _category_choices()
        if 'services' in self.fields:
            self.fields['services'].choices = _service_choices()


class NetboxForm(SectionForm):
    categories = forms.MultipleChoiceField()
    states = forms.MultipleChoiceField(choices=_state_choices())


class NetboxMaintenanceForm(SectionForm):
    categories = forms.MultipleChoiceField()
    states = forms.MultipleChoiceField(choices=_all_state_choices())


class ServiceForm(SectionForm):
    services = forms.MultipleChoiceField()
    states = forms.MultipleChoiceField(choices=_state_choices())


class ServiceMaintenanceForm(SectionForm):
    services = forms.MultipleChoiceField()
    states = forms.MultipleChoiceField(choices=_all_state_choices())


class ModuleForm(NetboxForm):
    pass


class ThresholdForm(SectionForm):
    categories = forms.MultipleChoiceField()


class LinkStateForm(SectionForm):
    categories = forms.MultipleChoiceField()


class SNMPAgentForm(SectionForm):
    categories = forms.MultipleChoiceField()


class AddSectionForm(forms.Form):
    """Form for adding a status section to be displayed"""
    section = forms.ChoiceField(
        choices=StatusPreference.SECTION_CHOICES,
        label='Section type',
    )

    def __init__(self, *args, **kwargs):
        super(AddSectionForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = 'status-preferences-addsection'
        self.helper.layout = Layout(
            Row(
                Column(Field('section', css_class='select2'),
                       css_class='medium-8'),
                Column(LabelSubmit('add_section', 'Add section',
                                   css_class='postfix'),
                       css_class='medium-4')
            )
        )
