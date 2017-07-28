import copy
from django.shortcuts import redirect
from django.http import Http404
from django.core.paginator import Paginator, InvalidPage
from django.template.response import TemplateResponse
from django.views.generic import View
from django.utils.translation import ugettext as _

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

    def render_to_response(self, context, template=None):
        return TemplateResponse( 
            request=self.request,
            template=self.get_template_names(),
            context=context
        )

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return self.render_to_response(context)

class ListView(TemplateView):

    allow_empty = True

    queryset = None
    paginate_by = None
    page_kwarg = 'page'

    def get_queryset(self):
        queryset = self.queryset._clone() if self.queryset else None
        if queryset:
            return queryset
        else:
            msg  = "'%s' must either define 'queryset'"
            msg += " or override 'get_queryset()'"
            raise ImproperlyConfigured(msg % self.__class__.__name__)

    def list_objects(self):
        return self.get_queryset()

    def paginate_queryset(self, queryset, page_size):
        paginator = self.get_paginator(queryset, page_size)
        page_kwarg = self.kwargs.get(self.page_kwarg)
        page_query_param = self.request.GET.get(self.page_kwarg)
        page_number = page_kwarg or page_query_param or 1
        try:
            page_number = int(page_number)
        except ValueError:
            if page_number == 'last':
                page_number = paginator.num_pages
            else:
                msg = "Page is not 'last', nor can it be converted to an int."
                raise Http404(_(msg))
        try:
            return paginator.page(page_number)
        except InvalidPage as exc:
            msg = 'Invalid page (%s): %s'
            raise Http404(_(msg % (page_number, str(exc))))

    def get_paginate_by(self):
        return self.paginate_by

    def get_paginator(self, queryset, page_size):
        return Paginator(queryset, page_size)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        object_list = self.list_objects()

        paginate_by = self.get_paginate_by()
        page = None
        if paginate_by:
            queryset = object_list._clone()
            page = self.paginate_queryset(queryset, paginate_by) 
            object_list = page.object_list

        if not self.allow_empty and not object_list.exists():
            raise Http404

        context['object_list'] = object_list
        context['page_obj'] = page
        context['is_paginated'] = page.has_other_pages() if page else None
        context['paginator'] = page.paginator if page else None

        return context

class SingleObjectMixin:

    lookup_field = 'pk'
    lookup_url_kwarg = None

    def lookup_object(self, pk, **kwargs):
        msg = "'%s' must override 'lookup_object(self, pk, **kwargs)'"
        raise ImproperlyConfigured(msg % self.__class__.__name__)

    def get_lookup_param(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        try:
            lookup = { self.lookup_field: self.kwargs[lookup_url_kwarg] }
        except KeyError:
            msg = "Lookup field '%s' was not provided in view kwargs to '%s'"
            raise ImproperlyConfigured(
                msg % (lookup_url_kwarg, self.__class__.__name__))
        return lookup

    def get_object(self):
        lookup = self.get_lookup_param()
        obj = self.lookup_object(**lookup)
        if obj:
            return obj
        else:
            raise Http404

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        if obj:
            context['object'] = obj
        return context

class DetailView(SingleObjectMixin, TemplateView):
    pass

class DeleteView(SingleObjectMixin, TemplateView):

    success_url = None

    def delete_object(self, **kwargs):
        obj = self.get_object()
        obj.delete()

    def post(self, request, *args, **kwargs):
       lookup = self.get_lookup_param() 
       self.delete_object(**lookup)
       return redirect(self.get_success_url())

    def get_success_url(self):
        try:
            return self.success_url
        except AttributeError:
            msg  = "No URL to redirect to. '%s' must provide 'success_url'."
            raise ImproperlyConfigured(msg % self.__class__.__name__)

class FormView(TemplateView):

    form_class = None
    success_url = None

    preview_template_name = None

    def is_preview(self):
        return (self.request.POST.get('preview', None) != None)

    def get_template_names(self):
        if self.is_preview():
            if not self.preview_template_name:
                msg  = "'%s' must either define 'template_name'"
                msg += " or override 'get_template_names()'"
                raise ImproperlyConfigured(msg % self.__class__.__name__)
            return [self.preview_template_name]
        return super().get_template_names()

    def get_form_class(self):
        if not self.form_class:
            msg  = "'%s' must either define 'form_class' or both 'model' and "
            msg += "'fields', or override 'get_form_class()'"
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

    def get_success_url(self):
        try:
            return self.success_url
        except AttributeError:
            msg  = "No URL to redirect to. '%s' must provide 'success_url'."
            raise ImproperlyConfigured(msg % self.__class__.__name__)

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
