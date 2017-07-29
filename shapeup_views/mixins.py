from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator, InvalidPage
from django.http import Http404
from django.utils.translation import ugettext as _

class MultipleObjectMixin:

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
        try:
            return self.get_queryset()
        except ImproperlyConfigured as e:
            msg  = "'%s' must either override 'list_objects()' or "
            msg += "'get_queryset()', or define 'queryset'"
            raise ImproperlyConfigured(msg % self.__class__.__name__)

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
