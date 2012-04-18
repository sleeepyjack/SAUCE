# -*- coding: utf-8 -*-
"""Sheet controller module

@author: moschlar
"""

import logging

# turbogears imports
from tg import expose, abort, tmpl_context as c, url, validate, flash, redirect, request
from tg.controllers import TGController

# third party imports
from tg.paginate import Page
#from tg.i18n import ugettext as _

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

# project specific imports
from sauce.lib.base import BaseController
from sauce.model import Sheet, DBSession
from sauce.controllers.assignments import AssignmentsController

log = logging.getLogger(__name__)

class SheetController(TGController):
    
    def __init__(self, sheet):
        
        self.sheet = sheet
        self.event = self.sheet.event
        
        self.assignments = AssignmentsController(sheet=self.sheet)
    
    @expose('sauce.templates.sheet')
    def index(self):
        '''Sheet details page'''
        
        return dict(page='sheets', bread=self.sheet, event=self.event, sheet=self.sheet)
    

class SheetsController(TGController):
    
    def __init__(self, event):
        
        self.event = event
    
    @expose('sauce.templates.sheets')
    def index(self, page=1):
        '''Sheet listing page'''
        
        #sheets = Page(Sheet.current_sheets(event=self.event, only_public=False), page=page, items_per_page=10)
        sheets = Page(self.event.current_sheets, page=page, items_per_page=10)
        previous_sheets = Page(self.event.previous_sheets, page=page, items_per_page=10)
        future_sheets = Page(self.event.future_sheets, page=page, items_per_page=10)
        
        return dict(page='sheets', bread=self.sheet, event=self.event, sheets=sheets, previous_sheets=previous_sheets, future_sheets=future_sheets)
    
    @expose()
    def _lookup(self, sheet_id, *args):
        '''Return SheetController for specified sheet_id'''
        
        try:
            sheet_id = int(sheet_id)
            sheet = Sheet.by_sheet_id(sheet_id, self.event)
        except ValueError:
            abort(400)
        except NoResultFound:
            abort(404)
        except MultipleResultsFound:
            abort(500)
        
        controller = SheetController(sheet)
        return controller, args
