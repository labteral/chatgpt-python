import requests
import tls_client
from urllib.error import HTTPError as HTTPTLSError
from chatgpt.errors import ChatgptError, ChatgptErrorCodes
from chatgpt.utils import random_sleep_time
from tls_client.sessions import TLSClientExeption

class HTTPSessionBase:
    DEFAULT_TIMEOUT = 300
    DEFAULT_HEADERS = {
        ""
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "en-US,en;q=0.5",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
        'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="107", "Google Chrome";v="107"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"'

    }

    def __init__(self, timeout=DEFAULT_TIMEOUT,proxy=None, cookies={}):
        """
        Args:
            timeout (int, optional): Request timeout time. Defaults to 300.
            proxy (str, optional): Wether it uses proxy or not. Defaults to None.
            cookies (dict, optional): Cookies to introduce. Defaults to {}.
        """        
        self._timeout = timeout
        self._proxy = proxy
        self._cookies = cookies


class HTTPTLSSession(HTTPSessionBase):

    def __init__(self, timeout=None, proxy=None, cookies=None, headers = {}):
        super().__init__(timeout,proxy,cookies)
        self._headers = headers
        self._session = tls_client.Session(client_identifier="chrome_107")
        if cookies is not None:
            self._session.cookies.update(cookies)

    def request(self, *args, headers={}, **kwargs):
        send_headers = {**self.DEFAULT_HEADERS}
        send_headers.update(self._headers)
        send_headers.update(headers)
        try:
            response = self._session.execute_request(
                *args, headers=send_headers, timeout_seconds=self._timeout, proxy=self._proxy, **kwargs)

        except TLSClientExeption as e:
            raise ChatgptError(str(e), ChatgptErrorCodes.CONNECTION_ERROR)
        
        random_sleep_time(0.7,1.4)
        if response.status_code == 200:
            return response
        else:
            raise HTTPTLSError(args[1], response.status_code,
                               response.text, response.headers, None)
    
    @property
    def cookies(self):
        return self._session.cookies.get_dict()

    @cookies.setter
    def cookies(self, cookies):
        return self._session.cookies.update(cookies)


class HTTPSession(HTTPSessionBase):

    def __init__(self, timeout=None, proxy=None, cookies=None, stream=True):
        super().__init__(timeout,proxy,cookies)
        self._session = requests.Session()
        self._session.headers.update(self.DEFAULT_HEADERS)
        self._session.stream = stream
        if cookies is not None:
            self._session.cookies.update(cookies)


    def request(self, *args, stream =None, **kwargs):
        try:
            response = self._session.request(
                *args, timeout=self._timeout, stream=stream, **kwargs)
            response.raise_for_status()
            return response
        except ConnectionError as ex:
            raise ChatgptError(str(ex), ChatgptErrorCodes.CONNECTION_ERROR)

    @property
    def headers(self):
        return self._session.headers

    @headers.setter
    def headers(self, headers):
        self._session.headers.update(headers)

    @property
    def cookies(self):
        return self._session.cookies.get_dict()

    @cookies.setter
    def headers(self, cookies):
        self._session.cookies.update(cookies)

