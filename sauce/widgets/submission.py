# -*- coding: utf-8 -*-
'''Submission widget for SAUCE

:class:`SubmissionValidator` handles the data which comes from either
the text fields or from an uploaded file.

@since: 17.03.2012
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

import logging

from chardet import detect

from tg import flash, request

import tw2.core as twc
import tw2.bootstrap.forms as twbf
import tw2.sqla as twsa
import tw2.jquery as twj

try:
    from tw2.jqplugins.chosen import ChosenSingleSelectField as _SingleSelectField
except ImportError:  # pragma: no cover
    from tw2.forms.bootstrap import SingleSelectField as _SingleSelectField

from sauce.widgets.lib import ays_js
from sauce.widgets.widgets import MediumTextField, MediumMixin, LargeTextArea, LargeSourceEditor, SourceDisplay
from sauce.model import Language, Assignment

log = logging.getLogger(__name__)


class SubmissionValidator(twc.Validator):

    def _validate_python(self, data, state=None):
        controller = request.controller_state.controller
        submission = controller.submission

        language = data['language']
        if language not in controller.assignment.allowed_languages:
            raise twc.ValidationError('The language %s is not allowed for this assignment' % (language))

        source, filename = u'', u''
        try:
            source = data['source']
            filename = (data['filename'] or
                'submission_%d.%s' % (submission.id, language.extension_src))
        except KeyError:
            pass

        # TODO
        try:
            source = data['source_file'].value
            try:
                source = unicode(source, encoding='utf-8')
            except UnicodeDecodeError as e:
                log.info('UnicodeDecodeError in Submission %r: %s',
                    submission, e)
                try:
                    det = detect(source)
                    log.debug('Encoding detection for Submission %r returned %r', submission, det)
                    source = unicode(source, encoding=det['encoding'])
                    if det['confidence'] < 0.66:
                        flash('Your submission source code was automatically determined to be '
                              'of encoding %s. Please check for wrongly converted characters!' % det['encoding'],
                              'info')
                except (UnicodeDecodeError, TypeError) as e:  # TypeError occurs when det['encoding'] is None
                    if isinstance(e, UnicodeDecodeError):
                        log.info('UnicodeDecodeError in submission %r with detected encoding %s: %s',
                            submission, det['encoding'], e)
                    elif isinstance(e, TypeError):
                        log.info('Could not determine encoding of Submission %r',
                            submission)
                    source = unicode(source, errors='ignore')
                    flash('Your submission source code failed to convert to proper Unicode. '
                          'Please verify your source code for replaced or missing characters. '
                          '(You should not be using umlauts in source code anyway...) '
                          'And even more should you not be submitting anything else but '
                          'source code text files here!',
                          'warning')
            filename = data['source_file'].filename
        except (KeyError, AttributeError):
            pass

#         data['source_file'] = None
        del data['source_file']
        data['source'] = source
        data['filename'] = filename
        return data


class LanguageSelectField(MediumMixin, _SingleSelectField):
    options = []
    prompt_text = None
    required = True
    validator = twsa.RelatedValidator(entity=Language)


class SubmissionForm(twbf.HorizontalForm):

    title = 'Submission'

    validator = SubmissionValidator

    id = twbf.HiddenField(validator=twc.IntValidator)
    assignment = twbf.HiddenField(validator=twsa.RelatedValidator(Assignment))

    filename = MediumTextField(
        placeholder=u'Enter a filename, if needed',
        validator=twc.StringLengthValidator,
        help_text=u'An automatically generated filename may not meet the '
        'language\'s requirements (e.g. the Java class name)',
    )
    scaffold_head = SourceDisplay()
    source = LargeSourceEditor(
        placeholder=u'Paste your source code here',
        validator=twc.StringLengthValidator(strip=False),
        fullscreen=True,
    )
    scaffold_foot = SourceDisplay()

    source_file = twbf.FileField(css_class='span7')

    language = LanguageSelectField()

    comment = LargeTextArea(
        placeholder=u'Comment on the above source code',
        validator=twc.StringLengthValidator,
        rows=3,
    )

    @classmethod
    def post_define(cls):
        if twj.jquery_js not in cls.resources:
            cls.resources.append(twj.jquery_js)
        if ays_js not in cls.resources:
            cls.resources.append(ays_js)

    def prepare(self):
        self.safe_modify('language')
        self.child.c.language.options = [(l.id, l.name) for l in self.value.assignment.allowed_languages]
        if len(self.value.assignment.allowed_languages) == 1:
            self.value.language = self.value.assignment.allowed_languages[0]

        try:
            self.safe_modify('source')
            self.child.c.source.mode = self.value.language.lexer_name
            # self.child.c.source.firstLineNumber = len(self.value.scaffold_head.splitlines()) + 1
        except AttributeError:
            pass
        try:
            self.safe_modify('scaffold_head')
            self.child.c.scaffold_head.mode = self.value.language.lexer_name
            # self.child.c.scaffold_head.filename = self.value.filename
            # self.child.c.scaffold_head.show = self.value.scaffold_show
        except AttributeError:
            pass
        try:
            self.safe_modify('scaffold_foot')
            self.child.c.scaffold_foot.mode = self.value.language.lexer_name
            # self.child.c.scaffold_foot.filename = self.value.filename
            # self.child.c.scaffold_foot.show = self.value.scaffold_show
            # self.child.c.scaffold_foot.firstLineNumber = len(self.value.scaffold_head.splitlines()) + len(self.value.source.splitlines()) + 2
        except AttributeError:
            pass

        super(SubmissionForm, self).prepare()

        self.add_call(twj.jQuery(twc.js_symbol('document')).ready(twc.js_symbol(u'''\
function () {
    var cm_head = $("%(scaffold_head)s + .CodeMirror")[0].CodeMirror;
    var cm_source = $("%(source)s + .CodeMirror")[0].CodeMirror;
    var cm_foot = $("%(scaffold_foot)s + .CodeMirror")[0].CodeMirror;

    var cm_head_cnt = cm_head.getDoc().lineCount();
    var cm_source_doc = cm_source.getDoc();

    function updateFootFirstLineNumber(instance, changeObj) {
        var lines = cm_head_cnt + cm_source_doc.lineCount() + 1;
        cm_foot.setOption('firstLineNumber', lines);
    }

    // Initially set firstLineNumber for source
    cm_source.setOption('firstLineNumber', cm_head_cnt + 1);

    // Initially set firstLineNumber for scaffold_foot
    updateFootFirstLineNumber();

    cm_source.on('changes', updateFootFirstLineNumber);
}''' % {'scaffold_head': self.child.c.scaffold_head.selector,
        'source': self.child.c.source.selector,
        'scaffold_foot': self.child.c.scaffold_foot.selector})))

        self.add_call(twj.jQuery(twc.js_symbol('document')).ready(twc.js_symbol(u'''\
function () {
    $("%(form)s").areYouSure();
    $("%(source)s + .CodeMirror")[0].CodeMirror.on('changes', function(instance) { instance.save(); });
}''' % {'form': self.selector or 'Form', 'source': self.child.c.source.selector})))
