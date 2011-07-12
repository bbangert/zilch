"""Reporting/Collector Utility functions"""
import datetime
import hashlib
import logging
import uuid

import pkg_resources

def lookup_versions(module_list, include_deps=False):
    """Given a list of modules, look up their versions and return
    a dict of the located libraries and their versions along with
    all dependencies
    
    """
    libs = {}
    check_list = module_list[:]
    for module in check_list:
        # Don't check modules we already recorded info for
        if module in libs:
            continue
        
        missing_lib = True
        library_name = module
        while missing_lib:
            if library_name in pkg_resources.working_set.by_key:
                missing_lib = False
                pkg = pkg_resources.working_set.by_key[library_name]
                libs[library_name] = pkg.version
                
                if include_deps:
                    # Add unchecked dependencies for lib lookup
                    unchecked_deps = [x.key for x in pkg.requires() if x.key not in libs]
                    check_list.extend(unchecked_deps)
            else:
                # If we're out of chunks to break off, escape
                if '.' not in library_name:
                    break
                library_name = '.'.join(library_name.split('.')[:-1])
    return libs


def construct_checksum(level=logging.ERROR, class_name='', traceback='', message='', **kwargs):
    checksum = hashlib.md5(str(level))
    checksum.update(class_name or '')
    if traceback:
        traceback = '\n'.join(traceback.split('\n')[:-2])
    message = traceback or message
    if isinstance(message, unicode):
        message = message.encode('utf-8', 'replace')
    checksum.update(message)
    return checksum.hexdigest()


def iter_tb(tb):
    while tb:
        # support for __traceback_hide__ which is used by a few libraries
        # to hide internal frames.
        if tb.tb_frame.f_locals.get('__traceback_hide__'):
            continue
        yield tb
        tb = tb.tb_next


def get_traceback_frames(tb):
    frames = []
    for tb in iter_tb(tb):
        filename = tb.tb_frame.f_code.co_filename
        function = tb.tb_frame.f_code.co_name
        lineno = tb.tb_lineno - 1
        module_name = tb.tb_frame.f_globals.get('__name__')
        frames.append({
            'id': id(tb),
            'filename': filename,
            'module': module_name,
            'function': function,
            'lineno': lineno + 1,
            # TODO: vars need to be references
            'vars': tb.tb_frame.f_locals,
        })
    return frames


def transform(value, stack=[], context=None):
    # TODO: make this extendable
    # TODO: include some sane defaults, like UUID
    # TODO: dont coerce strings to unicode, leave them as strings
    if context is None:
        context = {}
    objid = id(value)
    if objid in context:
        return '<...>'
    context[objid] = 1
    if any(value is s for s in stack):
        ret = 'cycle'
    transform_rec = lambda o: transform(o, stack + [value], context)
    if isinstance(value, (tuple, list, set, frozenset)):
        ret = type(value)(transform_rec(o) for o in value)
    elif isinstance(value, uuid.UUID):
        ret = repr(value)
    elif isinstance(value, datetime.datetime):
        ret = value.strftime('%Y-%m-%dT%H:%M:%S.%f')
    elif isinstance(value, datetime.date):
        ret = value.strftime('%Y-%m-%d')
    elif isinstance(value, dict):
        ret = dict((k, transform_rec(v)) for k, v in value.iteritems())
    elif isinstance(value, unicode):
        ret = to_unicode(value)
    elif isinstance(value, str):
        try:
            ret = str(value)
        except:
            ret = to_unicode(value)
    elif not isinstance(value, (int, bool)) and value is not None:
        # XXX: we could do transform(repr(value)) here
        ret = to_unicode(value)
    else:
        ret = value
    del context[objid]
    return ret


def to_unicode(value):
    try:
        value = unicode(force_unicode(value))
    except (UnicodeEncodeError, UnicodeDecodeError):
        value = '(Error decoding value)'
    except Exception: # in some cases we get a different exception
        try:
            value = str(repr(type(value)))
        except Exception:
            value = '(Error decoding value)'
    return value


def force_unicode(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Similar to smart_unicode, except that lazy instances are resolved to
    strings, rather than kept as lazy objects.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    # Handle the common case first, saves 30-40% in performance when s
    # is an instance of unicode. This function gets called often in that
    # setting.
    if isinstance(s, unicode):
        return s
    if strings_only and is_protected_type(s):
        return s
    try:
        if not isinstance(s, basestring,):
            if hasattr(s, '__unicode__'):
                s = unicode(s)
            else:
                try:
                    s = unicode(str(s), encoding, errors)
                except UnicodeEncodeError:
                    if not isinstance(s, Exception):
                        raise
                    # If we get to here, the caller has passed in an Exception
                    # subclass populated with non-ASCII data without special
                    # handling to display as a string. We need to handle this
                    # without raising a further exception. We do an
                    # approximation to what the Exception's standard str()
                    # output should be.
                    s = ' '.join([force_unicode(arg, encoding, strings_only,
                            errors) for arg in s])
        elif not isinstance(s, unicode):
            # Note: We use .decode() here, instead of unicode(s, encoding,
            # errors), so that if s is a SafeString, it ends up being a
            # SafeUnicode at the end.
            s = s.decode(encoding, errors)
    except UnicodeDecodeError, e:
        if not isinstance(s, Exception):
            raise UnicodeDecodeError(s, *e.args)
        else:
            # If we get to here, the caller has passed in an Exception
            # subclass populated with non-ASCII bytestring data without a
            # working unicode method. Try to handle this without raising a
            # further exception by individually forcing the exception args
            # to unicode.
            s = ' '.join([force_unicode(arg, encoding, strings_only,
                    errors) for arg in s])
    return s


def shorten(var):
    var = transform(var)
    MAX_LENGTH_LIST = 20
    MAX_LENGTH_STRING = 255
    if isinstance(var, basestring) and len(var) > MAX_LENGTH_STRING:
        var = var[:MAX_LENGTH_STRING] + '...'
    elif isinstance(var, (list, tuple, set, frozenset)) and len(var) > MAX_LENGTH_LIST:
        # TODO: we should write a real API for storing some metadata with vars when
        # we get around to doing ref storage
        # TODO: when we finish the above, we should also implement this for dicts
        var = list(var)[:MAX_LENGTH_LIST] + ['...', '(%d more elements)' % (len(var) - MAX_LENGTH_LIST,)]
    return var
