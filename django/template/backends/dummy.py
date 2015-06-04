# Since this package contains a "django" module, this is required on Python 2.
from __future__ import absolute_import

import errno
import io
import string

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.template import Origin, TemplateDoesNotExist
from django.utils.html import conditional_escape

from .base import BaseEngine
from .utils import csrf_input_lazy, csrf_token_lazy


class TemplateStrings(BaseEngine):

    app_dirname = 'template_strings'

    def __init__(self, params):
        params = params.copy()
        options = params.pop('OPTIONS').copy()
        if options:
            raise ImproperlyConfigured(
                "Unknown options: {}".format(", ".join(options)))
        super(TemplateStrings, self).__init__(params)

    def from_string(self, template_code):
        return Template(template_code)

    def get_template(self, template_name):
        tried = []
        for template_file in self.iter_template_filenames(template_name):
            try:
                with io.open(template_file, encoding=settings.FILE_CHARSET) as fp:
                    template_code = fp.read()
            except IOError as e:
                if e.errno == errno.ENOENT:
                    tried.append((
                        Origin(template_file, template_name, self),
                        'Source does not exist',
                    ))
                    continue
                raise

            return Template(template_code)

        else:
            raise TemplateDoesNotExist(template_name, tried=tried, backend=self)


class Template(string.Template):

    def render(self, context=None, request=None):
        return ''.join(self.stream(context, request))

    def stream(self, context=None, request=None):
        if context is None:
            context = {}
        else:
            context = {k: conditional_escape(v) for k, v in context.items()}
        if request is not None:
            context['csrf_input'] = csrf_input_lazy(request)
            context['csrf_token'] = csrf_token_lazy(request)
        yield self.safe_substitute(context)
