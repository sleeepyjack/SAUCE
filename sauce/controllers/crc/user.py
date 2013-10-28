# -*- coding: utf-8 -*-
'''CrudControllers for User entities and context-dependant "sub-classes"

@see: :mod:`sauce.controllers.crc.base`

@since: 12.11.2012
@author: moschlar
'''
#
## SAUCE - System for AUtomated Code Evaluation
## Copyright (C) 2013 Moritz Schlarb
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU Affero General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Affero General Public License for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from tg import flash, config, request, expose, tmpl_context
from tg.decorators import before_render

from sauce.controllers.crc.base import FilterCrudRestController
from sauce.model import Team, User, Lesson

from webhelpers.html.tags import link_to

from sauce.lib.misc import merge

import logging
log = logging.getLogger(__name__)

__all__ = ['TeamsCrudController', 'StudentsCrudController', 'TutorsCrudController']


_externalauth = config.get('externalauth', False)


#--------------------------------------------------------------------------------


def _submissions(filler, obj):
    '''Display submission link button for Users or Teams'''
    if filler.__entity__ is User:
        filterstr = '/user/%d' % obj.id
    elif filler.__entity__ is Team:
        filterstr = '/team/%d' % obj.id
    else:
        raise Exception('Wat?')
    return u'<a href="%s" style="white-space: pre;" class="btn btn-mini">'\
        '<i class="icon-inbox"></i>&nbsp;Submissions</a>' % (filler.hints['event'].url + '/submissions/' + filterstr)


#--------------------------------------------------------------------------------


def _email_team(filler, obj):
    '''Display mailto link button with team members email addresses'''
    return u'<a href="mailto:%s?subject=%%5BSAUCE%%5D" class="btn btn-mini"'\
        'onclick="return confirm(\'This will send an eMail to %d people. '\
        'Are you sure?\')">'\
        '<i class="icon-envelope"></i>&nbsp;eMail</a>' % (
            ','.join(s.email_address for s in obj.students), len(obj.students))


class TeamsCrudController(FilterCrudRestController):
    '''CrudController for Teams'''

    model = Team

    __table_options__ = {
        #'__omit_fields__': ['lesson_id'],
        '__field_order__': ['id', 'name', 'lesson_id', 'lesson', 'members', 'email', 'submissions'],
        '__search_fields__': ['id', 'lesson_id', 'name'],
        '__xml_fields__': ['lesson', 'members', 'email', 'submissions'],
        'lesson': lambda filler, obj: \
            link_to(obj.lesson.name, '../lessons/%d/edit' % obj.lesson.id),
        'members': lambda filler, obj: \
            ', '.join(link_to(student.display_name, '../students/%d/edit' % student.id) \
                for student in obj.members),
        'email': _email_team,
        'submissions': _submissions,
        '__base_widget_args__': {'sortList': [[3, 0], [1, 0]]},
    }
    __form_options__ = {
        '__omit_fields__': ['id'],
        '__field_order__': ['id', 'name', 'lesson', 'members'],
        '__dropdown_field_names__': ['user_name', '_name', 'name', 'title'],
    }


#--------------------------------------------------------------------------------


def set_password(user):
    '''Sets the password for user to a new autogenerated password and displays it via flash'''
#     from warnings import warn
#     warn('set_password', DeprecationWarning, stacklevel=2)
    password = user.generate_password()
    flash('Password for User %s set to: %s' % (user.user_name, password), 'info')
    return password


def _new_password(filler, obj):
    '''Display button for generating a new password'''
    return u'<a href="%d/password" class="btn btn-mini" style="white-space: pre;"'\
        'onclick="return confirm(\'This will generate a new, randomized '\
        'password for the User %s and show it to you. Are you sure?\')">'\
        '<i class="icon-random"></i><br />New&nbsp;password</a>' % (obj.id, obj.display_name)


def _email_address(filler, obj):
    '''Display mailto link button with users email address'''
    return u'<a href="mailto:%s?subject=%%5BSAUCE%%5D" style="white-space: pre;" class="btn btn-mini">'\
        '<i class="icon-envelope"></i>&nbsp;%s</a>' % (obj.email_address, obj.email_address)


class UsersCrudController(FilterCrudRestController):
    '''Base CrudController for Users

    Constructor will merge __table_options__ between this class and subclasses
    to allow customization without too much duplication.
    '''

    model = User
    menu_item = u'Users'

    __table_options__ = {
        '__omit_fields__': [
            'type', 'groups',
            'password', '_password',
            '_last_name', '_first_name',
            'created',
            'judgements',
            'teached_events',
            '_events',
        ] + (['new_password'] if _externalauth else []),
        '__field_order__': [
            'id',
            'user_name',
            '_display_name',
            'email_address',
            'teams', '_lessons',
            'tutored_lessons',
            'submissions',
        ] + ([] if _externalauth else ['new_password']),
        '__search_fields__': [
            'id', 'user_name', 'email_address',
        ],
#        '__headers__': {
#            'new_password': u'Password',
#            '_lessons': u'Lessons'},
        '__xml_fields__': ['email_address', 'teams', '_lessons', 'tutored_lessons', 'submissions', 'new_password'],
        'email_address': _email_address,
        'teams': lambda filler, obj: \
            ', '.join(link_to(team.name, '../teams/%d/edit' % team.id) \
                    for team in obj.teams if team in filler.query_modifiers['teams'](Team.query)),
        '_lessons': lambda filler, obj: \
            ', '.join(link_to(lesson.name, '../lessons/%d/edit' % lesson.id) \
                    for lesson in obj._lessons if lesson in filler.query_modifiers['_lessons'](Lesson.query)),
        'tutored_lessons': lambda filler, obj: \
            ', '.join(link_to(lesson.name, '../lessons/%d/edit' % lesson.id) \
                for lesson in obj.tutored_lessons if lesson in filler.query_modifiers['tutored_lessons'](Lesson.query)),
        'submissions': _submissions,
        'new_password': _new_password,
    }
    __form_options__ = {
        '__omit_fields__': [
            'id',
            'type', 'groups',
            'display_name',
            '_first_name', '_last_name',
            'password', '_password',
            'created',
            'submissions', 'judgements',
            'tutored_lessons', 'teached_events',
            'teams', '_lessons',
            '_events',
        ],
        '__field_order__': [
            'id',
            'user_name', '_display_name',
            'email_address',
#            'teams', '_lessons',
        ],
    }
    __setters__ = {
        'password': ('password', set_password),
    }

    def __init__(self, *args, **kwargs):
        '''Merge __table_options__ from parent class and child class'''
        self.__table_options__ = merge(UsersCrudController.__table_options__, self.__table_options__)
        super(UsersCrudController, self).__init__(*args, **kwargs)

    @staticmethod
    def warn_externalauth_edit(*args, **kw):
        '''Warn user that editing the profile is pretty useless'''
        self = request.controller_state.controller
        if self.model is User:
            flash('All profile changes made here will be overwritten when the users logs in the next time!', 'warn')

    @staticmethod
    def warn_externalauth_delete(*args, **kw):
        '''Warn that deleting the profile is pretty useless'''
        self = request.controller_state.controller
        if self.model is User:
            flash('The profile will be created again when the users logs in the next time!', 'warn')


class StudentsCrudController(UsersCrudController):
    '''CrudController for Students'''

    menu_item = u'Student'

    __table_options__ = {
        '__omit_fields__': [
            'tutored_lessons', 'teached_events',
        ],
        '__search_fields__': [
            ('teams', 'team_id'), ('lessons', 'lesson_id'),
        ],
        '__base_widget_args__': {
            'headers': {8: {'sorter': False}},
            'sortList': [[6, 0], [5, 0], [3, 0]],
        },
    }


class TutorsCrudController(UsersCrudController):
    '''CrudController for Tutors'''

    menu_item = u'Tutor'

    __table_options__ = {
        '__omit_fields__': [
            'teached_events',
            '_lessons', 'teams',
            ],
        '__search_fields__': [
            ('tutored_lessons', 'lesson_id'),
        ],
        '__base_widget_args__': {
            'headers': {7: {'sorter': False}},
            'sortList': [[5, 0], [3, 0]],
        },
    }


class TeachersCrudController(TutorsCrudController):
    '''CrudController for Teachers

    @deprecated: Use :class:`TutorsCrudController` instead
    '''

    menu_item = u'Teacher'

    def __init__(self, *args, **kw):
        '''Teachers are deprecated in favor of Tutors'''
        from warnings import warn
        warn('TeachersCrudController', DeprecationWarning, stacklevel=2)
        super(TeachersCrudController, self).__init__(*args, **kw)


if _externalauth:
    # Warn user that profile changes/deletions are pretty useless when external
    # authentication is used

    before_render(UsersCrudController.warn_externalauth_edit)(StudentsCrudController.edit)
    before_render(UsersCrudController.warn_externalauth_edit)(TutorsCrudController.edit)
    before_render(UsersCrudController.warn_externalauth_edit)(TeachersCrudController.edit)

    before_render(UsersCrudController.warn_externalauth_delete)(StudentsCrudController.get_delete)
    before_render(UsersCrudController.warn_externalauth_delete)(TutorsCrudController.get_delete)
    before_render(UsersCrudController.warn_externalauth_delete)(TeachersCrudController.get_delete)
