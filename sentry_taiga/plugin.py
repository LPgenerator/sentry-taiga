"""
sentry_taiga.plugin
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2015 by RochSystems.
:license: MIT, see LICENSE for more details.
"""

from django import forms
from sentry.plugins.bases.issue import IssuePlugin
from django.utils.translation import ugettext_lazy as _

from taiga import TaigaAPI

import sentry_taiga

class TaigaOptionsForm(forms.Form):
    taiga_url = forms.CharField(
        label=_('Taiga URL'),
        widget=forms.TextInput(attrs={'placeholder': 
                                      'e.g. https://taiga.example.com'}),
        help_text=_('Enter the URL for your Taiga server'),
        required=True)

    taiga_username = forms.CharField(
        label=_('Taiga User Name'),
        widget=forms.TextInput(attrs={'placeholder': 'e.g. user@example.com'}),
        help_text=_('Enter your Taiga User name'),
        required=True)

    taiga_password = forms.CharField(
        label=_('Taiga Password'),
        widget=forms.PasswordInput(attrs={'placeholder': 'e.g. your password'}),
        help_text=_('Enter your Taiga User password'),
        required=True)

    taiga_project = forms.CharField(
        label=_('Taiga Project Slug'),
        widget=forms.TextInput(attrs={'placeholder': 'e.g. project-slug'}),
        help_text=_('Enter your project slug.'),
        required=True)

class TaigaPlugin(IssuePlugin):
    author = 'skob via rochsystems'
    author_url = 'http://rochsystems.com/'
    version = sentry_taiga.VERSION
    description = "Integrate Taiga issues by linking a repository to a project"
    resource_links = [
        ('Bug Tracker', 'https://github.com/skob/sentry-taiga/issues'),
        ('Source', 'https://github.com/skob/sentry-taiga'),
    ]

    slug = 'taiga'
    title = _('Taiga')
    conf_title = title
    conf_key = 'taiga'
    project_conf_form = TaigaOptionsForm

    def is_configured(self, request, project, **kwargs):
        return bool(self.get_option('taiga_project', project))

    def get_new_issue_title(self, **kwargs):
        return _('Create Taiga US')

    def create_issue(self, request, group, form_data, **kwargs):

        url = self.get_option('taiga_url', group.project)
        username = self.get_option('taiga_username', group.project)
        password = self.get_option('taiga_password', group.project)
        project_slug = self.get_option('taiga_project', group.project)
        
        tg = TaigaAPI(host=url)

        try:
            tg.auth(username=username, password=password)
        except Exception as e:
            raise forms.ValidationError(_('Error Communicating '
                                        'with Taiga: %s') % (e,))

        project = tg.projects.get_by_slug(slug=project_slug)
        if project is None:
            raise forms.ValidationError(_('No project found in Taiga with slug %s') % 
                                        (project_slug,))

        default_us_status = project.default_us_status    
        if default_us_status is None:
            raise forms.ValidationError(_('Project %s has no default status. '
                'Set the default user story status in Taiga') % (project.name,))

        data = {
            'subject': form_data['title'],
            'status': default_us_status,
            'description': form_data['description'],
            'tags': map(lambda x:x.strip(), labels.split(","))}

        us = project.add_user_story(**data)

        return us.ref

    def get_issue_label(self, group, issue_id, **kwargs):
        return 'TG-%s' % issue_id

    def get_issue_url(self, group, issue_id, **kwargs):
        url = self.get_option('taiga_url', group.project)
        slug = self.get_option('taiga_project', group.project)

        return '%s/project/%s/us/%s' % (url, slug, issue_id)
