import copy
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect
from django.http import Http404
from django.template.response import TemplateResponse
from django.views.generic import View
from django.utils.translation import ugettext as _
from .mixins import SingleObjectMixin, MultipleObjectMixin

class TemplateView(View):

    template_name = None

    def get_template_names(self):
        if not self.template_name:
            msg  = "'%s' must either define 'template_name'"
            msg += " or override 'get_template_names()'"
            raise ImproperlyConfigured(msg % self.__class__.__name__)
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = copy.deepcopy(kwargs) 
        context['view'] = self
        return context

    def render_to_response(self, context):
        return TemplateResponse( 
            request=self.request,
            template=self.get_template_names(),
            context=context
        )

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return self.render_to_response(context)

class ListView(MultipleObjectMixin, TemplateView):
    pass

class DetailView(SingleObjectMixin, TemplateView):
    pass

class ProcessView(TemplateView):

    success_url = None

    def get_success_url(self):
        if not self.success_url:
            msg  = "No URL to redirect to. '%s' must provide 'success_url'."
            raise ImproperlyConfigured(msg % self.__class__.__name__)
        return self.success_url

class DeleteView(SingleObjectMixin, ProcessView):

    success_url = None

    def get_object(self, **kwargs):
        return None

    def delete_object(self, **kwargs):
        msg = "'%s' must override 'delete_object(self, **kwargs)'"
        raise NotImplementedError(msg % self.__class__.__name__)

    def post(self, request, *args, **kwargs):
       lookup = self.get_lookup_param() 
       self.delete_object(**lookup)
       return redirect(self.get_success_url())

class FormView(ProcessView):

    form_class = None

    preview_template_name = None

    def is_preview(self):
        return (self.request.POST.get('preview', None) != None)

    def get_template_names(self):
        if self.is_preview():
            if not self.preview_template_name:
                msg  = "'%s' must either define 'preview_template_name'"
                msg += " or override 'get_template_names()'"
                raise ImproperlyConfigured(msg % self.__class__.__name__)
            return [self.preview_template_name]
        return super().get_template_names()

    def get_form_class(self):
        if not self.form_class:
            msg  = "'%s' must either define 'form_class' "
            msg += "or override 'get_form_class()'"
            raise ImproperlyConfigured(msg % self.__class__.__name__)
        return self.form_class

    def get_form(self, data=None, files=None, **kwargs):
        cls = self.get_form_class()
        return cls(data=data, files=files, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def preview(self, form):
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = self.get_form(data=request.POST, files=request.FILES)
        if form.is_valid():
            if self.is_preview():
                return self.preview(form)
            else:
                return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        msg = "'%s' must override 'form_valid(self, form)'"
        raise NotImplementedError(msg % self.__class__.__name__)

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

class CreateView(FormView):

    def save_object(self, **kwargs):
        msg = "'%s' must override 'save_object(self, **kwargs)'"
        raise NotImplementedError(msg % self.__class__.__name__)

    def form_valid(self, form):
        self.object = self.save_object(**form.cleaned_data)
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if getattr(self, 'object', None):
            context['object'] = self.object
        return context

class UpdateView(SingleObjectMixin, FormView):

    def update_object(self, **kwargs):
        msg = "'%s' must override 'update_object(self, **kwargs)'"
        raise NotImplementedError(msg % self.__class__.__name__)

    def get_form(self, data=None, files=None, **kwargs):
        if not data:
            obj = self.get_object()
            fields = obj._meta.get_fields()
            data = { f.name: getattr(obj, f.name) for f in fields }
        return super().get_form(data=data, files=files, **kwargs)

    def form_valid(self, form):
        kwargs = copy.deepcopy(form.cleaned_data)
        kwargs.update(**self.get_lookup_param())
        self.update_object(**kwargs)
        return redirect(self.get_success_url())
