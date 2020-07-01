from typing import Optional, Union, Callable, Type, Iterable

DEFAULT_TIMEOUT = 15.0
FILE_CACHE_SIZE = 256
TEMPLATE_CACHE_SIZE = 256
TEMPLATE_PATH = "templates"
DEBUG = False
MAX_REQUEST_SIZE = 1024 * 1024 * 4

try:
    import regex as re
except ImportError:
    import re  # type: ignore
import pickle

pickle.DEFAULT_PROTOCOL = pickle.HIGHEST_PROTOCOL

import asyncio
import html
import time, datetime
import traceback

try:
    import uvloop # type: ignore

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

from sys import stderr
from os import getcwd as os_getcwd, stat as os_stat

# from os.path import join as path_join
from pathlib import Path
from functools import lru_cache
from email import utils as email_utils

from urllib.parse import unquote_plus, parse_qs, urlparse
from http import cookies as http_cookies
from mimetypes import guess_type
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import Queue, Manager, Event
from queue import Empty as EmptyQueue
from enum import Enum

pool = None
mgr = None

import os


class ParentProcessConnectionAborted(ConnectionAbortedError):
    pass


class WebException(Exception):
    def __init__(self, response):
        self.response = response


class ProcessType(Enum):
    """
    Classifications for the different process types.
    """

    main = 0
    pool = 1


class RouteType(Enum):
    """
    Classifications for the different ways routes can be processed.
    `sync`: Synchronous route.
    `sync_thread`: Sync route using thread pool.
    `asnc`: Async route.
    `asnc_local`: Async route that always runs in the default thread.
    `pool`: Multiprocessing-pooled route.
    `stream`: Multiprocessing-pooled route that yields results incrementally (and therefore may block).
    """

    sync = 0
    sync_nothread = 1
    asnc = 2
    asnc_local = 3
    pool = 4
    stream = 5


def _e(msg: str):
    """
    Shortcut for output to stderr.
    """
    if DEBUG:
        print(msg, file=stderr)


http_codes = {
    200: "OK",
    302: "Found",
    304: "Not Modified",
    404: "Not Found",
    451: "Unavailable For Legal Reasons",
    500: "Internal Server Error",
    503: "Service Unavailable",
}


def format_err(e):
    error = "".join(
        traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
    )
    return error


class ProcEnv:
    """
    Describes the process type for the running process. If you import proc_env you can inspect proc_type and pool to see what type of process your function is running in, and whether or not your have access to the process pool. (You only have access to the process pool from the main thread.)
    """

    def __init__(
        self,
        proc_type: Enum = ProcessType.main,
        pool: Optional[ProcessPoolExecutor] = None,
    ):
        self.proc_type = proc_type
        self.pool = pool


class Request:
    """
    Object created from a HTTP request.
    """

    def __init__(
        self, headers, init=False,
    ):
        if type(headers) is dict:
            self._headers: dict = headers
            self._raw_data = None
            self.request = (
                headers["REQUEST_METHOD"],
                headers["PATH_INFO"],
                headers["SERVER_PROTOCOL"],
            )
            content_length = headers.get("CONTENT_LENGTH")
            if content_length:
                self._body = headers["wsgi.input"].read(int(content_length))
            else:
                self._body = b""
            self._form = None
            self._cookies = None
            self._files = None
            self._param_dict = None
            return

        self.raw_data = headers
        self._headers = (
            self._form
        ) = self._body = self._files = self._cookies = self._param_dict = None
        if init:
            self.headers()

    @property
    def params(self):
        """
        Provide URL parameters as a dictionary.
        Use cached copy if available.
        """
        if self._param_dict:
            return self._param_dict
        self._param_dict = parse_qs(urlparse(self.headers["PATH_INFO"]).query)
        return self._param_dict

    @property
    def headers(self):
        """
        Provide headers as a dictionary.
        Use cached copy if available.
        """
        if self._headers:
            return self._headers

        self._headers, self._body = self._make_headers(self.raw_data)

        return self._headers

    # TODO: convert to simplecookie

    def _make_headers(self, data):
        """
        Takes a bytestream ("data"), splits headers from it, and returns a dict with the headers with the values for each header either as a string or a list.
        """
        headers = {}
        raw_headers, body = data.split(b"\r\n\r\n", 1)
        split_headers = raw_headers.split(b"\r\n")
        request_type = split_headers.pop(0)

        for _ in split_headers:
            k, v = _.split(b":", 1)
            k = str(k, "utf-8")
            v = str(v, "utf-8")
            k = k.upper().replace("-", "_")
            if k not in {"CONTENT_TYPE", "CONTENT_LENGTH", "CONTENT_DISPOSITION"}:
                k = f"HTTP_{k}"
            headers[k] = v.strip()

        if request_type != b"":
            (
                headers["REQUEST_METHOD"],
                headers["PATH_INFO"],
                headers["SERVER_PROTOCOL"],
            ) = str(request_type, "utf-8").split(" ")
        return headers, body

    def _make_subvalues(self, value):
        subvalues = {}
        for _ in value.split(";"):
            try:
                k, v = _.split("=")
            except ValueError:
                k = _
                v = None
            subvalues[k.strip()] = v
        return subvalues

    @property
    def cookies(self):
        if self._cookies:
            return self._cookies
        self.headers
        cookies = self.headers.get("HTTP_COOKIE")
        if cookies:
            self._cookies = self._make_subvalues(cookies)
        else:
            self._cookies = {}
        return self._cookies

    @property
    def req(self):
        try:
            return self.request
        except:
            self.headers
            return self.request

    @property
    def verb(self):
        try:
            return self.headers["REQUEST_METHOD"]
        except:
            self.headers
            return self.headers["REQUEST_METHOD"]

    @property
    def path(self):
        try:
            return self.headers["PATH_INFO"]
        except:
            self.headers
            return self.headers["PATH_INFO"]

    @property
    def protocol(self):
        try:
            return self.headers["SERVER_PROTOCOL"]
        except:
            self.headers
            return self.headers["SERVER_PROTOCOL"]

    @property
    def body(self):
        """
        Provide body as bytes.
        Use cached copy if available.
        """

        if self._body:
            return self._body

        self.headers

        return self._body

    @property
    def form(self):
        """
        Provide form data as a dictionary, if available.
        Returns None if the request has no form data.
        Use a cached copy if we can.
        """
        if self._form:
            return self._form

        if self.headers.get("CONTENT_TYPE", "").startswith(
            "application/x-www-form-urlencoded"
        ):
            self._form = self._urlencoded_form(self._body)
            return self._form

        if self.headers.get("CONTENT_TYPE", "").startswith("multipart/"):
            self._files, self._form = self._multipart_form(self.headers, self._body)
            return self._form

        self._form = None
        return None

    @property
    def files(self):
        if self._files:
            return self._files
        self.form
        return self._files

    def _urlencoded_form(self, body):
        form_split = body.split(b"&")
        form = {}
        for _ in form_split:
            __ = _.split(b"=")
            form[str(__[0], "utf-8")] = unquote_plus(str(__[1], "utf-8"))
        return form

    def _multipart_form(self, headers, body):
        files = {}
        form_data = {}

        header_line = headers["CONTENT_TYPE"].split(";")
        boundary = "--" + (header_line[1].split("=")[1])
        body_parts = body.split(bytes(boundary, "utf-8"))

        for _ in body_parts[1:-1]:
            headers, body = self._make_headers(_)
            content_type = headers.get("CONTENT_TYPE")
            if content_type is not None:
                disp = headers.get("CONTENT_DISPOSITION")
                subvalues = self._make_subvalues(disp)
                filename = subvalues["filename"].strip('"')
                name = subvalues["name"].strip('"')
                files[name] = (filename, body)
            else:
                disp = self._make_subvalues(headers.get("CONTENT_DISPOSITION"))
                name = disp["name"].strip('"')
                form_data[name] = str(body.strip(), "utf-8")

        return files, form_data

        # https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.2


class Response:
    """
    Generate a complex response object (a class instance) from a string object. Use `content_type` to set the Content-Type: header, `code` to set the HTTP response code, and pass a dict to `headers` to set other headers as needed.

    Use this when you want to perform complex manipulations on a response, like mutating its properties across multiple functions, before returning it to the client.
    """

    def __init__(
        self,
        body: str = "",
        code: Union[int, str] = 200,
        content_type: str = "text/html",
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
    ):
        self.body = body
        self.headers = headers
        self.code = code
        self.content_type = content_type

        if cookies is not None:
            self.cookies: Optional[
                http_cookies.SimpleCookie
            ] = http_cookies.SimpleCookie()
            for k, v in cookies.items():
                self.cookies[k] = v
                self.cookies[k]["Path"] = "/"
        else:
            self.cookies = None

    def as_bytes(self) -> bytes:
        return simple_response(
            self.body, self.code, self.content_type, self.headers, self.cookies
        )

    def start_response(self):
        headers = [("Content-Type", self.content_type)]

        if self.headers:
            for k, v in self.headers.items():
                headers.append((k, v))

        if self.cookies:
            headers.append(("Set-Cookie", self.cookies.output().split(":", 1)[1]))

        if isinstance(self.code, int):
            code_text = f"{self.code} {http_codes[self.code]}"
        else:
            code_text = self.code

        return [
            code_text,
            headers,
        ]


class Literal:
    def __init__(self, data: str):
        self.data = str(data)

    @property
    def esc(self):
        return html.escape(self.data, True)


class Unsafe:
    def __init__(self, data: str):
        self.data = str(data)

    def __str__(self):
        return html.escape(self.data, True)


class SimpleTemplate:
    def __init__(self, template: str):
        self.template = template.replace("{{", "{").replace("}}", "}")

    def render(self, *a, **ka):
        if a:
            new_a = []
            for _ in a:
                if isinstance(_, Literal):
                    new_a.append(_.data)
                else:
                    new_a.append(html.escape(str(_)))
            return self.template.format(*new_a)

        if ka:
            for k, v in ka.items():
                if isinstance(v, Literal):
                    ka[k] = v.data
                else:
                    ka[k] = html.escape(str(v))
            return self.template.format(**ka)


class Template:
    indents = re.compile(
        r"(if|elif|for|while|try|except|else|finally|with|def|class)\b"
    )
    _braces = re.compile(r"(\{\{!*.+?\}\})")
    _lit_braces = re.compile(r"(\{\{!(.*?)\}\})")

    def _indent(self):
        return " " * 4 * self.indent_level

    def _include(self, template, path):
        template_lines = template.split("\n")

        include_list = []

        for _ in template_lines:
            s_line = _.strip()
            if not s_line.startswith("%"):
                include_list.append(_)
                continue
            code_line = s_line.lstrip("%").lstrip()
            if not code_line.startswith("include "):
                include_list.append(_)
                continue
            else:
                include_file = code_line.split("include ")[1]
                with open(Path(path, include_file), encoding="utf=8") as f:
                    include_list.extend(self._include(f.read(), path))

        return include_list

    def __init__(
        self,
        template_str: str = None,
        name: str = "template",
        file: Optional[str] = None,
        path: Optional[str] = None,
    ):
        if path:
            self._path: Optional[str] = path
        else:
            self._path = TEMPLATE_PATH

        if file:
            self._file: Optional[str] = file
            self._template_str = None
        else:
            self._file = None
            self._template_str = str(template_str)

        self._compile()

    def _compile(self):
        if self._file:
            with open(Path(self._path, self._file), "r", encoding="utf-8") as f:
                template_str = f.read()
            self._template_name = Path(self._path, self._file)
        else:
            template_str = self._template_str
            self._template_name = "<string>"

        self.code_lines: list = []
        self.indent_level = 0
        self.code_lines.append("output = []")

        template_lines = self._include(template_str, self._path)

        current_string = []

        for _ in template_lines:
            s_line = _.strip()
            if not s_line.startswith("%"):
                t = re.split(self._braces, _)
                for x, n in enumerate(t):
                    # TODO: if there's an f-string in this,
                    # we need to handle it separately
                    if n.startswith("{{!"):
                        n = "{" + n[3:-2] + "}"
                    elif n.startswith("{{"):
                        n = "{Unsafe(" + n[2:-2] + ")}"
                    else:
                        n = n.replace("{", "{{").replace("}", "}}")
                    t[x] = n
                string_line = "".join(t)
                current_string.append(string_line)
                continue

            if current_string:
                string_line = r"\n".join(current_string)
                string_code_line = (
                    self._indent() + f"output.append(f'''{string_line}''')"
                )
                self.code_lines.append(string_code_line)
                current_string = []

            code_line = s_line.lstrip("%").lstrip()
            formatted_line = self._indent() + code_line

            if code_line.startswith("end"):
                self.indent_level -= 1
                continue

            if self.indents.match(code_line):
                self.indent_level += 1

            self.code_lines.append(formatted_line)

        if current_string:
            string_line = r"\n".join(current_string)
            string_code_line = self._indent() + f"output.append(f'''{string_line}''')"
            self.code_lines.append(string_code_line)

        self.code_lines.append(self._indent() + "__result__ = '\\n'.join(output)\n")

        self.code = "\n".join(self.code_lines)
        self.code_obj = compile(self.code, f"<template: {self._template_name}>", "exec")

    def render(self, **ka):
        if DEBUG:
            self._compile()
        ka.update({"Unsafe": Unsafe})
        exec(self.code_obj, None, ka)
        return ka["__result__"]


def parse_date(ims):
    # From Marcel Hellkamp's bottle.py
    try:
        ts = email_utils.parsedate_tz(ims)
        return time.mktime(ts[:8] + (0,)) - (ts[9] or 0) - time.timezone
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


def static_file(
    filename: str,
    path: str = os_getcwd(),
    max_age: int = 38400,
    last_modified: Optional[str] = None,
) -> Union[bytes, Response]:
    """
    Load static file from `path`, using `root` as the directory to start at.
    """
    file_type, encoding = guess_type(filename)
    full_path = Path(path, filename)
    try:
        with open(full_path, "rb") as file:
            stats = os_stat(full_path)
            if last_modified:
                last_mod_time = parse_date(last_modified)
                if last_mod_time <= stats.st_mtime:
                    return simple_response(b"", code="304 Not Modified")

            file_last_mod = email_utils.formatdate(stats.st_mtime, usegmt=True)

            return simple_response(
                file.read(),
                content_type=file_type,
                headers={
                    "Cache-Control": f"private, max-age={max_age}",
                    "Last-Modified": file_last_mod,
                    "Date": email_utils.formatdate(time.time(), usegmt=True),
                },
            )

    except FileNotFoundError as e:
        raise e


@lru_cache(FILE_CACHE_SIZE)
def cached_file(
    path: str, root: str = os_getcwd(), max_age: int = 38400
) -> Union[bytes, Response]:
    """
    Load a static file, but use the in-memory cache to avoid roundtrips to disk.
    """
    return static_file(path, root, max_age)


class SimpleResponse(bytes):
    pass


def simple_response(
    body,
    code: Union[int, str] = 200,
    content_type: Optional[str] = "text/html",
    headers: Optional[dict] = None,
    cookies: Optional[http_cookies.SimpleCookie] = None,
) -> SimpleResponse:
    """
    Generate a simple response object (a byte stream) from either a string or a bytes object. Use `content_type` to set the Content-Type: header, `code` to set the HTTP response code, and pass a dict to `headers` to set other headers as needed.

    Use this when you want to simply return a byte sequence as your response, without needing to manipulate the results too much. You can also use this to `yield` headers, and then pieces of a body (as simple `bytes` objects), when you want to return results incrementally.

    You should not use a `simple_response` in any situation where you might be returning results through WSGI.
    """

    if body is None:
        body_as_bytes = b""
    else:
        if type(body) is str:
            body_as_bytes = body.encode("utf-8")  # type: ignore
        else:
            body_as_bytes = body
        length = len(body_as_bytes)
        if not headers:
            headers = {}
        headers["Content-Length"] = length

    if headers is not None:
        header_str = "\r\n" + "\r\n".join([f"{k}: {v}" for k, v in headers.items()])
    else:
        header_str = ""

    if cookies is not None:
        cookie_str = "\r\n" + cookies.output()
    else:
        cookie_str = ""

    if isinstance(code, int):
        code_text = f"{code} {http_codes[code]}"
    else:
        code_text = code

    return SimpleResponse(
        bytes(
            f"HTTP/1.1 {code_text}\r\nContent-Type: {content_type}{header_str}{cookie_str}\r\n\r\n",
            "utf-8",
        )
        + body_as_bytes
    )


class Header(bytes):
    pass


def header(
    code: int = 200, content_type: str = "text/html", headers: Optional[dict] = None
):
    return Header(simple_response(None, code, content_type, headers))


path_re_str = "<([^>]*?)>"
path_re = re.compile(path_re_str)
path_replace = ".[]"


def redirect(location: str):
    return simple_response("", code=302, headers={"Location": location})


class Server:
    def __init__(self):
        self.static_routes: dict = {}
        self.dynamic_routes = []
        self.pool: Optional[ProcessPoolExecutor] = None
        self.threadpool = ThreadPoolExecutor()
        self.proc_env = ProcEnv()

    template_404 = SimpleTemplate("<h1>Path or file not found: {}</h1>")
    template_500 = SimpleTemplate("<h1>Server error in {}</h1><p><pre>{}</pre>")
    template_503 = SimpleTemplate("<h1>Server timed out after {} seconds in {}</h1>")

    def error_404(self, request: Request) -> Response:
        """
        Built-in 404: Not Found error handler.
        """
        return Response(self.template_404.render(request.path), code=404)

    def error_500(self, request: Request, error: Exception) -> Response:
        """
        Built-in 500: Server Error handler.
        """
        return Response(self.template_500.render(request.path, str(error)), code=500,)

    def error_503(self, request: Request) -> Response:
        """
        Built-in 503: Server Timeout handler.
        """
        return Response(
            self.template_503.render(DEFAULT_TIMEOUT, request.path), code=503,
        )

    def route(
        self,
        path: str,
        route_type: RouteType = RouteType.pool,
        action: Union[Iterable, str] = "GET",
        before=None,
        after=None,
    ):
        """
        Route decorator, used to assign a route to a function handler by wrapping the function. Accepts a `path`, an optional `route_type`, and an optional list of HTTP verbs (or a single verb string, default "GET") as arguments.
        """
        parameters = []
        route_regex = None

        path_match = re.finditer(path_re, path)

        for n in path_match:
            parameters.append(n.group(0)[1:-1])

        if parameters:
            for _ in path_replace:
                path = path.replace(_, "\\" + _)
            path = re.sub(path_re_str, "([^/]*?)", path)
            path += "$"
            route_regex = re.compile(path)

        if isinstance(action, str):
            action = [action]

        def decorator(callback):

            if route_regex:
                for _ in action:
                    self.add_dynamic_route(
                        route_regex, _, callback, route_type, parameters
                    )
            else:
                for _ in action:
                    self.add_route(path, _, callback, route_type)
            return callback

        return decorator

    def add_route(
        self,
        path: str,
        action: str,
        callback: Callable,
        route_type: RouteType = RouteType.pool,
    ):
        """
        Assign a static route to a function handler.
        """
        route = (callback, route_type)
        if not self.static_routes.get(path):
            self.static_routes[path] = {action: route}
        else:
            self.static_routes[path][action] = route

    def add_dynamic_route(
        self,
        regex_pattern,
        action: str,
        callback: Callable,
        route_type: RouteType = RouteType.pool,
        parameters: list = None,
    ):
        """
        Assign a dynamic route (with wildcards) to a function handler.
        """
        self.dynamic_routes.append(
            (regex_pattern, action, callback, route_type, parameters)
        )

    @classmethod
    def run_route_pool(cls, raw_env: bytes, func: Callable, *a, **ka):
        """
        Execute a function synchronously in the local environment. A copy of the HTTP request data is passed automatically to the handler as its first argument.
        """
        local_env = Request(raw_env)
        result = func(local_env, *a, **ka)
        if isinstance(result, Response):
            return result.as_bytes()
        return result

    @classmethod
    def run_route_pool_asnc(cls, raw_env: bytes, func: Callable, *a, **ka):
        """
        Execute a function synchronously in the local environment. A copy of the HTTP request data is passed automatically to the handler as its first argument.
        """
        local_env = Request(raw_env)
        result = asyncio.run(func(local_env, *a, **ka))
        if isinstance(result, Response):
            return result.as_bytes()
        return result

    @classmethod
    def run_route_pool_stream(
        cls, remote_queue: Queue, signal, raw_env: bytes, func: Callable, *a, **ka
    ):
        """
        Execute a function synchronously in the process pool, and return results from it incrementally.
        """
        local_env = Request(raw_env)
        for _ in func(local_env, *a, **ka):
            if signal.is_set():
                raise ParentProcessConnectionAborted
            remote_queue.put(_)
        remote_queue.put(None)

    async def start_server(self, host: str, port: int):
        """
        Launch the asyncio server with the master connection handler.
        """
        self.srv = await asyncio.start_server(
            self.connection_handler,
            host,
            port,
            # limit=MAX_REQUEST_SIZE
        )
        async with self.srv:  # type: ignore
            _e(f"Listening on {host}:{port}")
            await self.srv.serve_forever()

    def run_route_pool_wsgi(self, env, handler, *params):
        # Doesn't work yet
        loop = asyncio.get_event_loop()
        print(
            "r",
            loop.run_until_complete(
                loop.run_in_executor(self.pool, handler, env, *params)
            ),
        )

        # return handler(env, *params)

    def run(
        self,
        host: str = "localhost",
        port: int = 8000,
        workers: Union[bool, int, None] = True,
    ):
        """
        Run pixie_web on the stated hostname and port.
        """
        _e("Pixie-web 0.1")

        if workers is not None:
            if workers is True:
                self.use_process_pool()
            elif workers is False:
                pass
            else:
                self.use_process_pool(int(workers))

        try:
            asyncio.run(self.start_server(host, port))
        except KeyboardInterrupt:
            _e("Closing server with ctrl-C")
        except asyncio.CancelledError:
            _e("Closing due to internal loop shutdown")

    @classmethod
    def pool_start(cls):
        """
        Launched at the start of each pooled process. This modifies the environment data in the process to let any routes running in the process know that it's in a pool, not in the main process.
        """

        proc_env.proc_type = ProcessType.pool

    def use_process_pool(self, workers: Optional[int] = None):
        """
        Set up the process pool and ensure it's running correctly.
        """
        self.mgr = Manager()

        self.pool = ProcessPoolExecutor(
            max_workers=workers, initializer=Server.pool_start
        )

        from concurrent.futures.process import BrokenProcessPool

        try:
            self.pool.submit(lambda: None).result() # type: ignore
        except (OSError, RuntimeError, BrokenProcessPool):
            _e(
                "'run()' function must be invoked from within 'if __name__ == \"__main__\"' block to invoke multiprocessing. Defaulting to single-process pool."
            )
            self.pool = None
        else:
            _e(f"Using {self.pool._max_workers} processes")  # type: ignore

        self.proc_env.pool = self.pool

    def close_server(self):
        if self.srv is None:
            raise Exception(
                "No server to close on this instance. Use `ProcessType.main_async` to route the close operation to the main server."
            )
        self.srv.close()
        self.srv = None

    def application(self, environ, start_response):
        path = environ["PATH_INFO"].rstrip("/")
        verb = environ["REQUEST_METHOD"]

        if path == "":
            path = "/"

        parameters = []
        handler = result = None
        route_type = None

        try:
            handler, route_type = self.static_routes[path][verb]
        except KeyError:
            route_match = None
            for route in self.dynamic_routes:
                if verb != route[1]:
                    continue
                route_match = route[0].fullmatch(path)
                if route_match:
                    handler, route_type = route[2:4]
                    parameters = route_match.groups()

        if not handler:
            response = Response(f"Not found: {path}", code=404)
            start_response(*response.start_response())
            return [response.body.encode("utf-8")]

        try:
            if route_type == RouteType.asnc_local or route_type == RouteType.asnc:
                result = asyncio.run(handler(Request(environ), *parameters))

            elif route_type == RouteType.sync or route_type == RouteType.pool:
                result: Union[bytes, Response, str] = handler(
                    Request(environ), *parameters
                )

            else:
                raise NotImplementedError(f"{route_type} not implemented for WSGI")

        except Exception as e:
            return [bytes(f"Error: {format_err(e)}", encoding="utf-8")]

        if result is None:
            start_response("200 OK", [("Content-Type", "text/plain")])
            return [b""]
        elif isinstance(result, Response):
            start_response(*result.start_response())
            return [result.body.encode("utf-8")]
        elif isinstance(result, SimpleResponse):
            head, body = result.split(b"\r\n\r\n", 1)
            headers = head.split(b"\r\n")

            response_type, content_type = headers[0:2]
            protocol, code = response_type.split(b" ", 1)
            content_type = content_type.split(b": ", 1)

            out_headers = [("Content-Type", str(content_type[1], encoding="utf-8"))]

            for _ in headers[2:]:
                k, v = _.split(b": ", 1)
                out_headers.append((str(k, encoding="utf-8"), str(v, encoding="utf-8")))

            res = str(response_type.split(b" ", 1)[1], encoding="utf-8")
            start_response(res, out_headers)

            return [body]

        elif isinstance(result, bytes):
            response = Response(result)
            start_response(*response.start_response())
            return [result]
        else:
            start_response("500 Error", [("Content-Type", "text/plain")])
            return [
                b"Iterable not yet supported for WSGI; use Response or SimpleResponse"
            ]

    async def connection_handler(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """
        Reeads the data from the network connection, and attempts to find an appropriate route for it.
        """

        readline = reader.readline
        get_loop = asyncio.get_event_loop
        write = writer.write
        drain = writer.drain
        at_eof = reader.at_eof
        wait_for = asyncio.wait_for
        close = writer.close
        AsyncTimeout = asyncio.TimeoutError
        run_in_executor = get_loop().run_in_executor

        while True:

            # TODO: use stream limit in reader
            # split at first \n\n, assume rest is content

            action = raw_data = signal = content_length = route_type = result = None

            while True:
                # TODO: use .readuntil(sep)
                if at_eof():
                    close()
                    return

                _ = await readline()

                if raw_data is None:
                    raw_data = bytearray(_)
                    action = _.decode("utf-8").split(" ")
                    continue
                else:
                    raw_data.extend(_)

                if _ in {b"\r\n", b"\n"}:
                    break

                if content_length is None and _.decode("utf-8").lower().startswith("content-length:"):
                    content_length = int(_.decode("utf-8").split(":")[1])

                if len(raw_data) > MAX_REQUEST_SIZE:
                    content_length = MAX_REQUEST_SIZE+1
                    break

           
            if content_length:
                if content_length > MAX_REQUEST_SIZE:
                    write(simple_response(b"\n", code="413 Request too large"))
                    writer.close()
                    return
                raw_data.extend(await reader.readexactly(content_length))

            path = action[1].split("?", 1)[0].rstrip("/")
            verb = action[0]

            if path == "":
                path = "/"

            parameters = []
            handler = None

            try:
                handler, route_type = self.static_routes[path][verb]
            except KeyError:
                route_match = None
                for route in self.dynamic_routes:
                    if verb != route[1]:
                        continue
                    route_match = route[0].fullmatch(path)
                    if route_match:
                        handler, route_type = route[2:4]
                        parameters = route_match.groups()
                        break

            if not handler:
                write(self.error_404(Request(raw_data)).as_bytes())
                await drain()
                continue

            try:

                # Run with no pooling or async, in default process.
                # Single-threaded, blocking ALL other operations.

                if route_type is RouteType.sync_nothread:
                    result = handler(Request(raw_data), *parameters)

                # Run a sync function in an async thread.
                # Cooperative multitasking.

                elif route_type is RouteType.sync:
                    result = await wait_for(
                        run_in_executor(
                            self.threadpool, handler, Request(raw_data), *parameters
                        ),
                        DEFAULT_TIMEOUT,
                    )

                # Run async function in default process.
                # Single-threaded, nonblocking.

                elif route_type is RouteType.asnc_local:
                    result = await wait_for(
                        handler(Request(raw_data), *parameters), DEFAULT_TIMEOUT
                    )

                # Run async function in process pool.

                elif route_type is RouteType.asnc:
                    result = await wait_for(
                        run_in_executor(
                            self.pool,
                            Server.run_route_pool_asnc,
                            raw_data,
                            handler,
                            *parameters,
                        ),
                        DEFAULT_TIMEOUT,
                    )

                # Run non-async code in process pool.
                # Multi-processing, nonblocking.

                # Note that we pass `Server.run_route_pool`, not `self.run_route_pool`, because otherwise we can't correctly pickle the object. So we just use the class method that exists in the pool instance, since it doesn't need `self` anyway. If we DID need `self` over there, we could always get the server instance from the module-local server obj.

                elif route_type is RouteType.pool:
                    result = await wait_for(
                        run_in_executor(
                            self.pool,
                            Server.run_route_pool,
                            raw_data,
                            handler,
                            *parameters,
                        ),
                        DEFAULT_TIMEOUT,
                    )

                # Run incremental stream in process pool.

                elif route_type is RouteType.stream:

                    job_queue = self.mgr.Queue()
                    signal = self.mgr.Event()

                    job = self.pool.submit(
                        Server.run_route_pool_stream,
                        job_queue,
                        signal,
                        raw_data,
                        handler,
                        *parameters,
                    )

                    writer.transport.set_write_buffer_limits(0)

                    # We can't send an async queue object to the subprocess,
                    # so we use a manager queue and poll it every .1 sec

                    while True:

                        while True:
                            try:
                                _ = job_queue.get_nowait()
                            except EmptyQueue:
                                await asyncio.sleep(0.1)
                                continue
                            else:
                                break

                        if _ is None:
                            break

                        write(_)
                        await drain()

                    writer.close()
                    return

            except WebException as e:
                result = e.response.as_bytes()
            except FileNotFoundError:
                result = self.error_404(Request(raw_data))
            except AsyncTimeout:
                result = self.error_503(Request(raw_data))
            except Exception as e:
                result = self.error_500(Request(raw_data), format_err(e))

            try:
                if isinstance(result, SimpleResponse):
                    write(result)
                elif isinstance(result, Response):
                    write(result.as_bytes())
                elif isinstance(result, bytes):
                    write(result)
                elif result is None:
                    write(simple_response(b""))
                else:
                    for _ in result:
                        write(_)
                        await drain()
                    writer.close()
                    return

                await drain()

                # possible pattern to adopt to avoid backpressure:
                # await asyncio.wait_for(p.communicate(), 2)
                # except asyncio.TimeoutError as e:

            except ConnectionAbortedError:
                if signal:
                    signal.set()
                writer.close()
                return


server = Server()
route = server.route
run = server.run
proc_env = server.proc_env
