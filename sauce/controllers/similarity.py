# -*- coding: utf-8 -*-
"""Similarity controller module

"""

import logging
from difflib import SequenceMatcher

import matplotlib
matplotlib.use('Agg')  # Only backend available in server environments
import pylab
from ripoff import all_pairs, dendrogram, distances

from itertools import combinations
from functools import partial

# turbogears imports
from tg import expose, abort, flash, cache, tmpl_context as c, redirect
#from tg import redirect, validate, flash

# third party imports
#from tg.i18n import ugettext as _
#from repoze.what import predicates
from repoze.what.predicates import Any, has_permission
from pygmentize import Pygmentize

# project specific imports
from sauce.lib.base import BaseController
from sauce.model import Assignment, Submission
from sauce.lib.helpers import udiff
from sauce.lib.auth import has_teacher, has_teachers
from sauce.lib.menu import menu
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

log = logging.getLogger(__name__)

similarity_combined = lambda a, b: distances.combined(a or u'', b or u'')


def rgb(v, cmap_name='RdYlGn'):
    '''Get CSS rgb representation from color map with name'''
    cmap = pylab.get_cmap(cmap_name)
    (r, g, b, _) = cmap(v)
    return 'rgb(' + ','.join('%d' % int(x * 255) for x in (r, g, b)) + ')'


class SimilarityController(BaseController):

    def __init__(self, assignment):
        self.assignment = assignment
        self.submissions = sorted((s for s in self.assignment.submissions if s.source),
            key=lambda s: s.id)

        self.key = str(self.assignment.id)
        if self.submissions:
            self.key += '_' + '-'.join(str(s.id) for s in self.submissions)
            self.key += '_' + max(self.submissions, key=lambda s: s.modified)\
                .modified.strftime('%Y-%m-%d-%H-%M-%S')

        self.allow_only = Any(has_teacher(self.assignment),
                              has_teacher(self.assignment.sheet),
                              has_teacher(self.assignment.sheet.event),
                              has_teachers(self.assignment.sheet.event),
                              has_permission('manage'),
                              msg=u'You are not allowed to access this page.'
                              )

    def _before(self, *args, **kwargs):
        '''Prepare tmpl_context with navigation menus'''
        c.sub_menu = menu(self.assignment)

    def get_similarity(self):

        def calc():
            log.debug('Calculating similarity matrix for key %s...' % self.key)
            return all_pairs([s.source for s in self.submissions])

        simcache = cache.get_cache('similarity')
        matrix = simcache.get_value(key=self.key, createfunc=calc, expiretime=7 * 24 * 60 * 60)  # 7 days
        return matrix

    @expose()
    def index(self, *args, **kw):
        redirect(self.assignment.url + '/similarity/table', *args, **kw)

    @expose('sauce.templates.similarity')
    def table(self, cmap_name='RdYlGn', *args, **kw):
        c.rgb = partial(rgb, cmap_name=cmap_name)
        c.url = self.assignment.url + '/similarity'
        matrix = self.get_similarity()
        return dict(page='assignment', view='table',
            assignment=self.assignment, matrix=matrix,
            submissions=self.submissions)

    @expose('sauce.templates.similarity')
    def list(self, cmap_name='RdYlGn', *args, **kw):
        c.rgb = partial(rgb, cmap_name=cmap_name)
        c.url = self.assignment.url + '/similarity'

        matrix = self.get_similarity()

        l = sorted((((a, b), matrix[i, j])
                for (i, a), (j, b) in combinations(enumerate(self.submissions), 2)),
            key=lambda x: x[1])

        return dict(page='assignment', view='list',
            assignment=self.assignment,
            submissions=self.submissions, l=l)

    @expose(content_type="image/png")
    def dendrogram(self):
        return dendrogram(self.get_similarity(),
            leaf_label_func=lambda i: unicode(self.submissions[i].id),
            leaf_rotation=45)

    @expose('sauce.templates.similarity_diff')
    def diff(self, *args, **kw):
        c.rgb = rgb
        c.pygmentize = Pygmentize(linenos=False)
        try:
            a = Submission.query.filter_by(id=int(args[0])).one()
            b = Submission.query.filter_by(id=int(args[1])).one()
        except ValueError:
            abort(400)
        except IndexError:
            abort(400)
        except NoResultFound:
            abort(404)
        except MultipleResultsFound:
            log.warn('', exc_info=True)
            abort(500)
        else:
            return dict(page='assignment', view='diff',
                assignment=self.assignment, x=distances.combined(a.source or u'', b.source or u''),
                a=a, b=b, source=udiff(a.source, b.source, unicode(a), unicode(b)))
