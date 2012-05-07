# -*- coding: utf-8 -*-
"""Assignment controller module

@author: moschlar
"""

import logging
from datetime import datetime

# turbogears imports
from tg import expose, request, abort,  url, redirect, tmpl_context as c, flash, TGController
from tg.decorators import require

# third party imports
#from tg.paginate import Page
#from tg.i18n import ugettext as _
from repoze.what.predicates import Any, not_anonymous, has_permission
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

# project specific imports
from sauce.lib.auth import is_public, has_teacher
from sauce.model import Assignment, Submission, DBSession

log = logging.getLogger(__name__)

class AssignmentController(TGController):
    
    def __init__(self, assignment):
        
        self.assignment = assignment
        self.sheet = assignment.sheet
        self.event = self.sheet.event
        
        c.assignment = self.assignment
        
        self.allow_only = Any(is_public(self.assignment),
                              has_teacher(self.assignment),
                              has_teacher(self.sheet),
                              has_teacher(self.event),
                              has_permission('manage'),
                              msg=u'This Assignment is not public'
                              )
    
    def _before(self, *args, **kwargs):
        '''Prepare tmpl_context with breadcrumbs'''
        c.breadcrumbs = self.assignment.breadcrumbs
    
    @expose('sauce.templates.assignment')
    def index(self, page=1):
        '''Assignment detail page'''
        
        try:
            submissions = Submission.by_assignment_and_user(self.assignment, request.user).all()
            #submissions = Page(submissions, page=page, items_per_page=10)
        except:
            submissions = []
        
        return dict(page='assignments', event=self.event, assignment=self.assignment, submissions=submissions)
    
    @expose()
    @require(not_anonymous(msg=u'Only logged in users can create Submissions'))
    def submit(self):
        '''Create new submission for this assignment'''
        
        if not request.teacher and not self.assignment.is_active:
            flash('This assignment is not active, you may not create a submission', 'warning')
            redirect(url(self.assignment.url))
        
        submission = Submission(assignment=self.assignment, user=request.user,
                                created=datetime.now())
        DBSession.add(submission)
        try:
            DBSession.flush()
        except:
            log.warn('Error creating new submission', exc_info=True)
            flash('Error creating new submission', 'error')
            DBSession.rollback()
            redirect(url(self.assignment.url))
        else:
            redirect(url(submission.url))

class AssignmentsController(TGController):
    
    def __init__(self, sheet):
        
        self.sheet = sheet
        self.event = sheet.event
    
    def _before(self, *args, **kwargs):
        '''Prepare tmpl_context with breadcrumbs'''
        c.breadcrumbs = self.sheet.breadcrumbs
    
    @expose('sauce.templates.assignments')
    def index(self, page=1):
        ''''Assignment listing page'''
        
        assignments = self.sheet.assignments
        
        return dict(page='assignments', event=self.sheet.event, assignments=assignments)
    
    @expose()
    def _lookup(self, assignment_id, *args):
        '''Return AssignmentController for specified assignment_id'''
        
        try:
            assignment_id = int(assignment_id)
            assignment = Assignment.by_assignment_id(assignment_id, self.sheet)
        except ValueError:
            flash('Invalid Assignment id: %s' % assignment_id,'error')
            abort(400)
        except NoResultFound:
            flash('Assignment %d not found' % assignment_id,'error')
            abort(404)
        except MultipleResultsFound:
            log.error('Database inconsistency: Assignment %d' % assignment_id, exc_info=True)
            flash('An error occurred while accessing Assignment %d' % assignment_id,'error')
            abort(500)
        
        controller = AssignmentController(assignment)
        return controller, args
