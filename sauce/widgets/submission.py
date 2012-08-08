# -*- coding: utf-8 -*-
'''
Created on 17.03.2012

@author: moschlar
'''
import tw2.core as twc
import tw2.forms as twf
import tw2.bootstrap as twb
try:
    from tw2.jqplugins.chosen import ChosenSingleSelectField as SingleSelectField
except ImportError:
    from tw2.bootstrap import SingleSelectField


class SubmissionForm(twb.HorizontalForm):

    title = 'Submission'

    id = twf.HiddenField(validator=twc.IntValidator)
    assignment_id = twf.HiddenField(validator=twc.IntValidator)

    filename = twb.TextField(placeholder=u'Enter a filename, if needed',
        help_text=u'An automatically generated filename may not meet the '\
        'language\'s requirements (e.g. the Java class name)',
        css_class='span3')
    source = twb.TextArea(placeholder=u'Paste your source code here',
        css_class='span7', rows=10)
    source_file = twb.FileField(css_class='span7')

    language_id = SingleSelectField(options=[], prompt_text=None,
        css_class='span3',
        required=True, validator=twc.IntValidator(required=True))

    def prepare(self):
        self.child.c.language_id.options = [(l.id, l.name) for l in self.value.assignment.allowed_languages]
        super(SubmissionForm, self).prepare()
