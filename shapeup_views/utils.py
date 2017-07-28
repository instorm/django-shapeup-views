def build_query_interface(seed):

    def query_interface(category, selector, *, append_self=False):
        category = seed.get(category, None)
        interface = category.get(selector, None) if category else None
        def method_interface(self, **kwargs):
            return interface(**kwargs)
        return method_interface if append_self else interface

    return query_interface

