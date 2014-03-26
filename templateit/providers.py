# -*- coding: utf-8 -*-
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound
import jinja2.ext
import os


class TemplateProvider(object):

    _template_dirs = []

    def __init__(self, *args, **kwargs):
        self._env = self._create_env(*args, **kwargs)

    def _create_env(self, *args, **kwargs):
        raise NotImplementedError()

    def _get_template(self, *args, **kwargs):
        raise NotImplementedError()

    def render_to_string(self, *args, **kwargs):
        raise NotImplementedError()


class JinjaTemplateProvider(TemplateProvider):

    def __init__(self, template_dirs, **extra_options):
        super(JinjaTemplateProvider, self).__init__(template_dirs,
                                                    **extra_options)

    def _create_env(self, template_dirs, **extra_options):
        env = Environment(loader=FileSystemLoader(template_dirs),
                          extensions=[jinja2.ext.i18n, jinja2.ext.with_],
                          autoescape=True, **extra_options)
        env.install_gettext_callables(gettext=lambda s: s,
                                      ngettext=lambda s: s)
        return env

    def get_template(self, template, globals=None, env=None):
        env = env or self._env
        if isinstance(template, Template):
            return template
        elif isinstance(template, basestring):
            try:
                return env.get_template(template, globals=globals)
            except TemplateNotFound, e:
                raise TemplateNotFound(str(e))
        for t in template:
            try:
                return env.get_template(t, globals=globals)
            except TemplateNotFound:
                continue
        raise TemplateNotFound(template)

    def render_to_string(self, template, context=None):
        template = self.get_template(template)
        context = dict(context or {})
        return template.render(context)

    def _register_function(self, tag_type, function, name):
        assert tag_type in ['global', 'filter']
        if name is None:
            name = function.__name__
        getattr(self._env, {'filter': 'filters',
                            'global': 'globals'}[tag_type])[name] = function

    def register_filter(self, function, name=None):
        self._register_function('filter', function, name)

    def register_global(self, function, name=None):
        self._register_function('global', function, name)

    def register_template_dir(self, template_dir):
        new_dirs = set(os.listdir(template_dir))
        for existing in self._template_dirs:
            if new_dirs.intersection(set(os.listdir(existing))):
                raise ValueError(
                    'There are overlapping directories '
                    'with existing templates: %s' %
                        new_dirs.intersection(set(os.listdir(template_dir))))
        self._template_dirs.append(template_dir)
        self._env.loader = FileSystemLoader(self._template_dirs)
