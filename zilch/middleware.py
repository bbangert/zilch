"""WSGI Middleware for Zilch reporting"""
import sys

import zilch.client


class ZilchMiddleware(object):
    """Error handling middleware
    
    Captures exceptions, and reports them with
    :func:`~zilch.client.capture_exception`. Includes the URL, the exception,
    and the WSGI environ as the ``extra``.
    
    """
    def __init__(self, application, global_conf=None, **kw):
        self.application = application
        global_conf = global_conf or {}
        self.tags = global_conf.get('tags', []) or kw.get('tags', [])
        recorder_host = global_conf.get('zilch.recorder_host') or kw.get('zilch.recorder_host')
        if recorder_host:
            zilch.client.recorder_host = recorder_host
    
    def __call__(self, environ, start_response):
        """The WSGI application interface."""
        # We want to be careful about not sending headers twice,
        # and the content type that the app has committed to (if there
        # is an exception in the iterator body of the response)
        if environ.get('paste.throw_errors'):
            return self.application(environ, start_response)
        environ['paste.throw_errors'] = True

        try:
            sr_checker = ResponseStartChecker(start_response)
            app_iter = self.application(environ, sr_checker)
            return self.make_catching_iter(app_iter, environ, sr_checker)
        except:
            exc_info = sys.exc_info()
            try:
                start_response('500 Internal Server Error',
                               [('content-type', 'text/html; charset=utf8')],
                               exc_info)
                # @@: it would be nice to deal with bad content types here
                response = self.exception_handler(exc_info, environ)
                if isinstance(response, unicode):
                    response = response.encode('utf8')
                return [response]
            finally:
                # clean up locals...
                exc_info = None

    def make_catching_iter(self, app_iter, environ, sr_checker):
        if isinstance(app_iter, (list, tuple)):
            # These don't raise            
            return app_iter
        return CatchingIter(app_iter, environ, sr_checker, self)

    def exception_handler(self, exc_info, environ):
        data = {}
        cgi_vars = data['CGI Variables'] = {}
        wsgi_vars = data['WSGI Variables'] = {}
        hide_vars = ['paste.config', 'wsgi.errors', 'wsgi.input',
                     'wsgi.multithread', 'wsgi.multiprocess',
                     'wsgi.run_once', 'wsgi.version',
                     'wsgi.url_scheme']
        for name, value in environ.items():
            if name.upper() == name:
                if value:
                    cgi_vars[name] = value
            elif name not in hide_vars:
                wsgi_vars[name] = value
        if environ['wsgi.version'] != (1, 0):
            wsgi_vars['wsgi.version'] = environ['wsgi.version']
        proc_desc = tuple([int(bool(environ[key]))
                           for key in ('wsgi.multiprocess',
                                       'wsgi.multithread',
                                       'wsgi.run_once')])
        wsgi_vars['wsgi process'] = self.process_combos[proc_desc]
        wsgi_vars['application'] = self.application
        if 'weberror.config' in environ:
            data['Configuration'] = dict(environ['weberror.config'])
        
        zilch.client.capture_exception("HTTPException", exc_info=exc_info,
                                       extra=data, tags=self.tags)
        
        return """<html><head><title>Server Error</title></head>
                  <body><h1>Server Error</h1>An error occurred.</body>
                  </html>"""

    process_combos = {
        # multiprocess, multithread, run_once
        (0, 0, 0): 'Non-concurrent server',
        (0, 1, 0): 'Multithreaded',
        (1, 0, 0): 'Multiprocess',
        (1, 1, 0): 'Multi process AND threads (?)',
        (0, 0, 1): 'Non-concurrent CGI',
        (0, 1, 1): 'Multithread CGI (?)',
        (1, 0, 1): 'CGI',
        (1, 1, 1): 'Multi thread/process CGI (?)',
        }


class ResponseStartChecker(object):
    def __init__(self, start_response):
        self.start_response = start_response
        self.response_started = False

    def __call__(self, *args):
        self.response_started = True
        self.start_response(*args)


class CatchingIter(object):

    """
    A wrapper around the application iterator that will catch
    exceptions raised by the a generator, or by the close method, and
    display or report as necessary.
    """

    def __init__(self, app_iter, environ, start_checker, error_middleware):
        self.app_iterable = app_iter
        self.app_iterator = iter(app_iter)
        self.environ = environ
        self.start_checker = start_checker
        self.error_middleware = error_middleware
        self.closed = False

    def __iter__(self):
        return self

    def next(self):
        if self.closed:
            raise StopIteration
        try:
            return self.app_iterator.next()
        except StopIteration:
            self.closed = True
            close_response = self._close()
            if close_response is not None:
                return close_response
            else:
                raise StopIteration
        except:
            self.closed = True
            close_response = self._close()
            exc_info = sys.exc_info()
            response = self.error_middleware.exception_handler(
                exc_info, self.environ)
            if close_response is not None:
                response += (
                    '<hr noshade>Error in .close():<br>%s'
                    % close_response)

            if not self.start_checker.response_started:
                self.start_checker('500 Internal Server Error',
                               [('content-type', 'text/html')],
                               exc_info)

            return response

    def close(self):
        # This should at least print something to stderr if the
        # close method fails at this point
        if not self.closed:
            self._close()

    def _close(self):
        """Close and return any error message"""
        if not hasattr(self.app_iterable, 'close'):
            return None
        try:
            self.app_iterable.close()
            return None
        except:
            close_response = self.error_middleware.exception_handler(
                sys.exc_info(), self.environ)
            return close_response

def make_error_middleware(app, global_conf, **kw):
    if 'zilch.recorder_host' not in global_conf and 'zilch.recorder_host' not in kw:
        raise Exception("No ZeroMQ recorder_host configured.")
    return ZilchMiddleware(app, global_conf=global_conf, **kw)
