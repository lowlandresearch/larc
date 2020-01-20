import urllib
import functools
import logging
import pprint
from typing import Callable, List

import requests
from toolz.curried import (
    pipe, curry, partial, concatv, compose, map, filter, merge
)
from pyrsistent import pmap

from .common import (
    maybe_pipe, vmap, maybe_first, do_nothing, is_dict, vcall, Null,
)

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class ResponseError(ValueError):
    pass

class TokenAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, request):
        request.headers['Authorization'] = 'Bearer {}'.format(self.token)
        return request

class Api:
    def __init__(self, base_url, auth, session, *, method_kw=None):
        self.base_url = base_url
        self.auth = auth
        self.session = session
        self.method_kw = method_kw or {}

    def __call__(self, *parts, **kw):
        return Endpoint(
            self, parts, **merge(self.method_kw, kw)
        )

def link_next(response):
    return maybe_pipe(
        requests.utils.parse_header_links(
            response.headers.get('Link', '')
        ),
        filter(lambda d: d.get('rel', '').lower() == 'next'),
        maybe_first,
        lambda d: d['url'],
    )

def method_logger(name, method, *, log_func=None):
    @functools.wraps(method)
    def wrapper(*a, **kw):
        (log_func or log.debug)(f'{name.upper()}: {kw}')
        return method(*a, **kw)
    return wrapper

def namespace_data(data):
    def ns_dict(ns, d):
        return pipe(
            d.items(),
            vmap(lambda k, v: (f'{ns}[{k}]', v)),
            dict,
        )
    if is_dict(data):
        return pipe(
            data.items(),
            vmap(lambda k, v: ns_dict(k, v) if is_dict(v) else {k: v}),
            vcall(merge),
        )
    return data
                    
class Endpoint:
    def __init__(self, api, parts, **kwargs):
        self.api = api
        self.parts = tuple(parts)

        self.kwargs = pipe(
            merge(
                {'url': self.url, 'auth': self.api.auth},
                kwargs,
            ),
            pmap,
        )

        for name in ['get', 'post', 'put', 'delete', 'head',
                     'options', 'patch']:
            setattr(
                self, name, self.method(name, **self.kwargs)
            )
            setattr(
                self, f'maybe_{name}', self.maybe_method(name, **self.kwargs)
            )

    def __call__(self, *parts, **kw):
        return Endpoint(
            self.api, tuple(concatv(self.parts, parts)), **kw
        )

    def method(self, name, **orig_kw):
        def caller(*args, **kw):
            method = getattr(self.api.session, name)
            kw = merge(orig_kw, kw)
            if 'data' in kw:
                kw['data'] = pipe(
                    kw.pop('data'),
                    namespace_data,
                )
            # Preserve JSON data passed in to Api object
            if 'json' in self.api.method_kw:
                kw['json'] = merge(self.api.method_kw['json'],
                                   kw.get('json', {}))
            return method_logger(name, method)(*args, **kw)
        return caller

    def maybe_method(self, name, **orig_kw):
        class Outcome:
            def __init__(self, ok, result, *errors):
                self.ok = ok
                self.result = result
                self.errors = errors

            def __bool__(self):
                return bool(self.ok)

        def caller(*a, **kw):
            try:
                return Outcome(True, self.method(name, **orig_kw)(*a, **kw))
            except OSError as error:
                return Outcome(False, Null, error)
        return caller
        
    @property
    def url(self):
        base = self.api.base_url
        if not base.endswith('/'):
            base += '/'
        return urllib.parse.urljoin(
            base, '/'.join(pipe(self.parts, map(str)))
        )

    @curry
    def iter(self, method, *, url=None,
             iter_f=lambda resp: resp.json(),
             link_next_f=link_next, **requests_kw):
        response = getattr(self, method)(**(
            merge(requests_kw, {'url': url} if url else {})
        ))
        if response.status_code != 200:
            content = response.content.decode()
            raise ResponseError(
                f'Response code error: {response.status_code}\n\n'
                f'{content[:200]}\n'
                '...\n'
                '...\n'
                f'{content[-200:]}'
            )

        for value in iter_f(self, response):
            yield value

        next_url = link_next(response)
        if next_url:
            yield from self.iter(
                method, url=next_url, iter_f=iter_f, **requests_kw
            )

class ResourceEndpoint(Endpoint):
    def __init__(self, endpoint: Endpoint, data: dict, form_key: str):
        self.data = data
        self.form_key = form_key

        super().__init__(endpoint.api, endpoint.parts)
        
def empty_dict(*a, **kw):
    return {}

class IdResourceEndpoint(Endpoint):
    def __init__(self, parent: Endpoint, data: dict, form_key: str,
                 id_key: str,
                 meta_f: Callable[[dict], dict] = empty_dict,
                 unpack_f: Callable[[dict], dict] = do_nothing,
                 single_unpack_f: Callable[[dict], dict] = do_nothing):
        self.parent = parent
        self.data = merge(data, {'metadata': meta_f(data)})
        self.form_key = form_key
        self.id_key = id_key
        self.meta_f = meta_f
        self.unpack_f = unpack_f
        self.single_unpack_f = single_unpack_f

        if id_key not in data:
            log.error(f'ID key {id_key} not in data: {data}')

        super().__init__(parent.api, parent.parts + (data[id_key],))

    @classmethod
    @curry
    def from_multiple_response(cls, parent: Endpoint,
                               response: requests.Response, *,
                               form_key=None, id_key='id',
                               meta_f=empty_dict,
                               unpack_f=do_nothing,
                               single_unpack_f=do_nothing):
        for d in unpack_f(response.json()):
            yield cls(parent, d, form_key, id_key, meta_f=meta_f,
                      unpack_f=unpack_f, single_unpack_f=single_unpack_f)

    @classmethod
    @curry
    def from_single_response(cls, parent: Endpoint,
                             response: requests.Response, *,
                             form_key=None, id_key='id',
                             meta_f=do_nothing,
                             unpack_f=do_nothing,
                             single_unpack_f=do_nothing):
        data = unpack_f(response.json())
        return cls(parent, data, form_key, id_key, meta_f=meta_f,
                   unpack_f=unpack_f, single_unpack_f=single_unpack_f)

    def refresh(self, **get_kw):
        return IdResourceEndpoint(
            self.parent, self.single_unpack_f(self.get(**get_kw).json()),
            self.form_key, self.id_key, meta_f=self.meta_f,
            unpack_f=self.unpack_f, single_unpack_f=self.single_unpack_f,
        )

@curry
def update_endpoint(endpoint: IdResourceEndpoint, update: dict, *,
                    body_transform=do_nothing,
                    get_kw=None, do_refresh=True):
    update = dict(body_transform(update))
    response = endpoint.put(
        json=({endpoint.form_key: update}
              if endpoint.form_key is not None else update)
    )

    if response.status_code in range(200, 300):
        if do_refresh:
            return endpoint.refresh(**(get_kw or {}))
        return endpoint

    log.error(
        f'There was an error after updating endpoint {endpoint.url}:\n'
        '\n'
        f'Update dict: \n{pprint.pformat(update)}\n'
        '\n'
        f'Response code: {response.status_code}'
        '\n'
        'Response:\n'
        f'{response.content[:1000]}'
    )
    return endpoint


# ----------------------------------------------------------------------
# Caching logic
#
#
# It is assumed that each type of Endpoint has lists of other
# Endpoints associated with them. For a given parent Endpoint and a
# child resource name, the cache stores a list of child objects.
#
# ----------------------------------------------------------------------

_cache = {}
def memoize_key(parent_endpoint: Endpoint, resource_name: str):
    return (parent_endpoint.url, resource_name)

@curry
def memoize_resources(parent_endpoint: Endpoint, resource_name: str,
                      resources: List[Endpoint]):
    global _cache
    _cache[memoize_key(parent_endpoint, resource_name)] = resources
    return resources

def cache_get(parent_endpoint: Endpoint, resource_name: str, default=None):
    return _cache.get(memoize_key(parent_endpoint, resource_name), default)
    
def cache_remove(parent_endpoint: Endpoint, resource_name: str, default=None):
    return cache_remove_by_key(
        memoize_key(parent_endpoint, resource_name), default,
    )
    
def cache_remove_by_key(key, default=None):
    return _cache.pop(key, default)
    
def cache_has_key(parent_endpoint: Endpoint, resource_name: str):
    return memoize_key(parent_endpoint, resource_name) in _cache

def total_cache_reset():
    log.debug('TOTAL CACHE RESET')
    global _cache
    _cache = {}

def reset_cache_by_endpoint(parent_endpoint: Endpoint):
    for (url, resource_name) in tuple(_cache):
        if parent_endpoint.url == url:
            log.debug(f'Reset {resource_name} cache for {url}')
            cache_remove(parent_endpoint, resource_name)

def reset_cache_by_resource_name(resource_name: str):
    for (url, name) in tuple(_cache):
        if name == resource_name:
            log.debug(f'Reset {resource_name} cache for {url}')
            cache_remove_by_key((url, name))

def reset_cache_for_endpoint_by_resource_name(parent_endpoint: Endpoint,
                                              resource_name: str):
    cache_remove(parent_endpoint, resource_name)

def get_id_resource(resource_name: str, *,
                    form_key: str = None,
                    id_key: str = 'id', meta_f=empty_dict,
                    unpack_f=do_nothing, single_unpack_f=do_nothing,
                    help=None, **iter_kw):
    @curry
    def getter(parent_endpoint: IdResourceEndpoint, id: (int, str), **get_kw):
        return pipe(
            parent_endpoint(resource_name, id).get(**get_kw),
            IdResourceEndpoint.from_single_response(
                parent_endpoint(resource_name),
                form_key=form_key, id_key=id_key, unpack_f=unpack_f,
                meta_f=meta_f, single_unpack_f=single_unpack_f,
            )
        )
    getter.__doc__ = help or ''

    return getter

def get_id_resources(resource_name: str, *, form_key: str = None,
                     id_key: str = 'id', meta_f=empty_dict,
                     unpack_f=do_nothing, single_unpack_f=do_nothing,
                     help=None, memo=False, **iter_kw):
    def getter(parent_endpoint: IdResourceEndpoint, *, do_memo=True):
        if (memo and do_memo) and cache_has_key(parent_endpoint,
                                                resource_name):
            return cache_get(parent_endpoint, resource_name)

        return pipe(
            parent_endpoint(resource_name).iter(
                'get', **merge(
                    {'iter_f': compose(
                        IdResourceEndpoint.from_multiple_response(
                            form_key=form_key, id_key=id_key,
                            meta_f=meta_f, unpack_f=unpack_f,
                            single_unpack_f=single_unpack_f,
                        ),
                    )},
                    iter_kw
                )
            ),
            tuple,
            memoize_resources(parent_endpoint, resource_name),
        )
    getter.__doc__ = help or ''

    getter.reset_cache = partial(
        reset_cache_for_endpoint_by_resource_name,
        resource_name=resource_name,
    )
    getter.reset_cache.__doc__ = f'''
    Reset the "{resource_name}" cache for a given Endpoint.
    '''

    return getter

@curry
def new_id_resource(resource_name: str, *,
                    form_key: str = None, id_key: str = 'id',
                    get_kw=None, help: str = None, memo=False,
                    meta_f=empty_dict, unpack_f=do_nothing,
                    single_unpack_f=do_nothing,
                    post_unpack_f=do_nothing,
                    body_transform=do_nothing):
    def creator(parent_endpoint: Endpoint, body: dict):
        body = dict(body_transform(body))
        body = {form_key: body} if form_key is not None else body
        log.debug(f'Request body: {body}')
        response = parent_endpoint(resource_name).post(json=body)

        if response.status_code in range(200, 300):
            post_data = post_unpack_f(response.json())
            new_response = parent_endpoint(
                resource_name, post_data[id_key]
            ).get(**(get_kw or {}))
            if new_response.status_code in range(200, 300):
                cache_remove(parent_endpoint, resource_name)
                return IdResourceEndpoint(
                    parent_endpoint(resource_name),
                    new_response.json(),
                    form_key=form_key, id_key=id_key,
                    meta_f=meta_f,
                    unpack_f=unpack_f, single_unpack_f=single_unpack_f,
                )

            log.error(
                f'There was an error after creating {resource_name} object:\n'
                f'  body: {body}\n'
                f'  form_key: {form_key}\n'
                f'  id_key: {id_key}\n'
                'Response:\n'
                f'{new_response.content[:1000]}'
            )

        log.error(
            f'There was an error creating {resource_name} object:\n'
            f'  body: {body}\n'
            f'  form_key: {form_key}\n'
            f'  id_key: {id_key}\n'
            'Response:\n'
            f'{response.content[:1000]}'
        )
    creator.__doc__ = help or ''
    return creator

