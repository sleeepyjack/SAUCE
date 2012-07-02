# -*- coding: utf-8 -*-
"""Lessons controller module

@author: moschlar
"""

import logging
from itertools import combinations_with_replacement
from difflib import SequenceMatcher, unified_diff
from collections import defaultdict

# turbogears imports
from tg import expose, abort, request, tmpl_context as c, flash, TGController
#from tg import redirect, validate, flash

# third party imports
#from tg.i18n import ugettext as _
from tgext.crud import CrudRestController
from tgext.crud.utils import SortableTableBase
from sprox.fillerbase import TableFiller
from sprox.tablebase import TableBase
from repoze.what.predicates import Any, has_permission
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

# project specific imports
from sauce.lib.auth import has_teachers, has_teacher
from sauce.lib.helpers import link, highlight, udiff
from sauce.model import Lesson, Team, Submission, Assignment, Student, Teacher, DBSession
from sauce.controllers.crc import (FilteredCrudRestController, TeamsCrudController,
                                   StudentsCrudController, LessonsCrudController,
                                   TeachersCrudController)
from sauce.widgets import SubmissionTable, SubmissionTableFiller
from sauce.model.user import student_to_lesson, student_to_team
from pygmentize.widgets import Pygmentize

log = logging.getLogger(__name__)


class SubmissionsController(TGController):

    def __init__(self, lesson, *args, **kw):
        self.lesson = lesson

        self.table = SubmissionTable(DBSession)
        self.table_filler = SubmissionTableFiller(DBSession, lesson=self.lesson)

    @expose('sauce.templates.submissions')
    def index(self, view='by_team', *args, **kw):
        c.table = self.table
#        value_list = self.table_filler.get_value(**kw)
#        submissions = self.table_filler.get_value(**kw)

        values = {'sheets': [], 'teams': [], 'students': []}

        if view not in ('by_sheet', 'by_team', 'by_student'):
            view = 'by_team'

        if view == 'by_sheet':
            sheets = sorted(self.lesson.event.sheets, key=lambda s: (s.end_time, s.start_time), reverse=True)
            #log.debug(sheets)
            for sheet in sheets:
                s = []
                for assignment in sheet.assignments:
                    s.extend(self.table_filler.get_value(assignment_id=assignment.id))
                sheet.submissions_ = s
            values['sheets'] = sheets
        elif view == 'by_team':
            teams = sorted(self.lesson.teams, key=lambda t: t.name)
            #log.debug(teams)
            teamstudents = set()  # Will hold all the students that are in a team
            for team in teams:
                s = []
                for student in team.students:
                    s.extend(self.table_filler.get_value(user_id=student.id))
                team.submissions_ = s
                teamstudents |= set(team.students)
            values['teams'] = teams
            # remaining students without team
            #TODO: If student is in a team AND in the lesson, he gets displayed twice
            students = sorted(set(self.lesson._students) - teamstudents, key=lambda s: s.display_name)
            #log.debug(students)
            for student in students:
                student.submissions_ = self.table_filler.get_value(user_id=student.id)
            values['students'] = students
        elif view == 'by_student':
            students = sorted(self.lesson.students, key=lambda s: s.display_name)
            #log.debug(students)
            for student in students:
                student.submissions_ = self.table_filler.get_value(user_id=student.id)
            values['students'] = students

        return dict(page='event', view=view, values=values,
                    #value_list=value_list
                    )

    @expose('sauce.templates.similarity')
    def similarity(self, assignment=None, *args, **kw):
        matrix = defaultdict(lambda: defaultdict(dict))
        sm = SequenceMatcher()
        try:
            assignment = Assignment.query.filter_by(id=int(assignment)).one()
        except Exception as e:
            log.debug('', exc_info=True)
            flash(u'Assignment "%s" does not exist' % assignment, 'error')
        else:
            if assignment.submissions:
                for (s1, s2) in combinations_with_replacement(assignment.submissions, 2):
                    sm.set_seqs(s1.source or u'', s2.source or u'')
                    matrix[s1][s2]['real_quick_ratio'] = matrix[s2][s1]['real_quick_ratio'] = sm.real_quick_ratio()
                    matrix[s1][s2]['quick_ratio'] = matrix[s2][s1]['quick_ratio'] = sm.quick_ratio()
                    matrix[s1][s2]['ratio'] = matrix[s2][s1]['ratio'] = sm.ratio()
        return dict(page='event', assignment=assignment, matrix=matrix)

    @expose()
    def diff(self, *args, **kw):
        if len(args) != 2:
            abort(404)
        try:
            a = Submission.query.filter_by(id=int(args[0])).one()
            b = Submission.query.filter_by(id=int(args[1])).one()
        except:
            raise
        else:
            pyg = Pygmentize(full=True, title='Submissions %d and %d, Similarity: %.2f' % (a.id, b.id, SequenceMatcher(a=a.source or u'', b=b.source or u'').ratio()))
            return pyg.display(lexer='diff', source=udiff(a.source, b.source, unicode(a), unicode(b)))

class LessonController(LessonsCrudController):

    model = Lesson
    title = 'Lesson'

    def __init__(self, lesson, **kw):
        self.lesson = lesson

        super(LessonController, self).__init__(inject=dict(teacher=request.teacher, event=self.lesson.event),
                                               filter_bys=dict(id=self.lesson.id),
                                               menu_items={'./%d/' % (self.lesson.lesson_id): 'Lesson',
                                                           './%d/teams' % (self.lesson.lesson_id): 'Teams',
                                                           './%d/students' % (self.lesson.lesson_id): 'Students',
                                                           #'./%d/submissions' % (self.lesson.lesson_id): 'Submissions',
                                                           },
                                               btn_new=False, btn_delete=False, path_prefix='.',
                                               **kw)

        menu_items = {'../%d/' % (self.lesson.lesson_id): 'Lesson',
                      '../%d/teams' % (self.lesson.lesson_id): 'Teams',
                      '../%d/students' % (self.lesson.lesson_id): 'Students',
                      #'../%d/submissions' % (self.lesson.lesson_id): 'Submissions',
                     }

        self.teams = TeamsCrudController(inject=dict(lesson=self.lesson),
                                         filters=[Team.lesson == self.lesson],
                                         menu_items=menu_items,
                                         **kw)
        self.students = StudentsCrudController(inject=dict(_lessons=[self.lesson]),
                                               query_modifier=lambda qry: qry.join(student_to_lesson).filter_by(lesson_id=self.lesson.id).union(qry.join(student_to_team).join(Team).filter_by(lesson_id=self.lesson.id)).distinct().order_by(Student.id),
                                               menu_items=menu_items,
                                               **kw)
        self.teachers = TeachersCrudController(filters=[Teacher.lessons.contains(self.lesson)],
                                               menu_items=menu_items,
                                               **kw)

        self.submissions = SubmissionsController(self.lesson,
                                                 DBSession, menu_items=menu_items, **kw)

        # Allow access for event teacher and lesson teacher
        self.allow_only = Any(has_teacher(self.lesson.event),
                              has_teacher(self.lesson),
                              has_permission('manage'),
                              msg=u'You have no permission to manage this Lesson'
                              )

    @expose()
    def new(self):
        '''No new lessons are to be created.'''
        abort(403)


class LessonsController(TGController):

    def __init__(self, event):
        self.event = event

        self.allow_only = Any(has_teacher(self.event),
                              has_teachers(self.event),
                              has_permission('manage'),
                              msg=u'You have no permission to manage Lessons for this Event'
                              )

    @expose()
    def index(self):
        '''Lesson listing page'''
        return dict(page='lessons', event=self.event)

    @expose()
    def _lookup(self, lesson_id, *args):
        '''Return LessonController for specified lesson_id'''

        try:
            lesson_id = int(lesson_id)
            lesson = Lesson.by_lesson_id(lesson_id, self.event)
        except ValueError:
            flash('Invalid Lesson id: %s' % lesson_id, 'error')
            abort(400)
        except NoResultFound:
            flash('Lesson %d not found' % lesson_id, 'error')
            abort(404)
        except MultipleResultsFound:
            log.error('Database inconsistency: Lesson %d' % lesson_id, exc_info=True)
            flash('An error occurred while accessing Lesson %d' % lesson_id, 'error')
            abort(500)

        controller = LessonController(lesson)
        return controller, args

