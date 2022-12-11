import urllib

from urllib.error import HTTPError as HTTPTLSError
from chatgpt.sessions import HTTPTLSSession
from chatgpt.utils import random_sleep_time
from .errors import ChatgptError, ChatgptErrorCodes

class OpenAIAuthentication:

    def __init__(self, session: HTTPTLSSession):
        self.session = session
       
   
    def _request_login(self):
        response = self.session.request(
            "GET", "https://chat.openai.com/auth/login")
            
        return response

    def _request_providers(self):
        response = self.session.request(
            "GET", "https://chat.openai.com/api/auth/providers")
        return response.json()

    def _request_csrf(self):
        response = self.session.request(
            "GET", "https://chat.openai.com/api/auth/csrf",)
        return response.json()

    def _request_signin(self, url, csrfToken: dict):
        payload = "callbackUrl=%2F&csrfToken={}&json=true".format(csrfToken)
        response = self.session.request("POST", "{}?prompt=login".format(url),
                                        headers={
                                            "Content-Type": "application/x-www-form-urlencoded",
                                            "Accept": "*/*"
        },
            data=payload)
        return response.json()

    def _request_authorize(self, url: str):
        try:

            self.session._headers = {
                "Upgrade-Insecure-Requests": "1"
            }
            response = self.session.request("GET", url)
        except HTTPTLSError as e:
            if e.code == 302:
                if "state" in str(e):
                    return str(e).split("state=")[1].split("\">")[0]
            raise e
        raise HTTPTLSError(url, 200, "Bad authorize request",
                           response.headers, None)
    

    def _request_login_identifier(self, state: str):
        url = "https://auth0.openai.com/u/login/identifier?state={}".format(
            state)
        response = self.session.request("GET", url)
        if "alt=\"captcha\"" in response.text:
            raise HTTPTLSError(
                url, 400, "Captcha needed", response.headers, None)
        return state

    def _request_login_identifier_post(self, state, email):
        try:
            url = "https://auth0.openai.com/u/login/identifier?state={}".format(
                state)

            email = urllib.parse.quote_plus(email)
            payload = "action=default&is-brave=false&js-available=false&state={}&username={}&webauthn-available=false&webauthn-platform-available=false".format(
                state, email)
            response = self.session.request("POST", url, data=payload, headers={
                                            "Content-Type": "application/x-www-form-urlencoded",
                                            })

        except HTTPTLSError as e:
            if e.code == 302:
                return state
            else:
                raise e
        raise HTTPTLSError(url, 200, "Bad authorize request",
                           response.headers, None)

    def _request_login_password(self, state):
        url = "https://auth0.openai.com/u/login/password?state={}".format(
            state)
        self.session.request("GET", url)
        return state

    def _request_login_password_post(self, state, email: str, password: str):
        url = "https://auth0.openai.com/u/login/password?state={}".format(
            state)
        email = urllib.parse.quote_plus(email)
        password = urllib.parse.quote_plus(password)
        payload = "action=default&password={}&state={}&username={}".format(
            password, state, email)
        try:
            response = self.session.request("POST", url, data=payload, headers={
                                            "Content-Type": "application/x-www-form-urlencoded",
                                            "Accept": "*/*"
                                            })
        except HTTPTLSError as e:
            if e.code == 302:
                return str(e).split("state=")[1].split("\">")[0]
            else:
                raise e
        raise HTTPTLSError(url, 200, "Bad authorize request",
                           response.headers, None)

    def _request_authorize_access_token(self, state):
        response = self.session.request("GET", "https://auth0.openai.com/authorize/resume?state={}".format(
            state), allow_redirects=True)
        return response.cookies.get("__Secure-next-auth.session-token")

    def get_session(self):
        """Get the actual gpt session.
        """
        try:
            response = self.session.request(
                "GET", "https://chat.openai.com/api/auth/session")
            return response.json()
        except HTTPTLSError as e:
            raise ChatgptError(
                "Error getting the session. You may have a wrong access token; try to login again or insert an access_token yourself.",
                ChatgptErrorCodes.LOGIN_ERROR) from e

    def login(self, username, password):
        """Get the access token for chatgpt

        Args:
            username (str): Email for chatgpt
            password (str): Password for chatgpt
        """
        try:
            self._request_login()
            try:
                chatgpt_session = self.get_session()
                if chatgpt_session:
                    return chatgpt_session
            except Exception:
                pass
            providers = self._request_providers()
            csrf = self._request_csrf()
            sigin = self._request_signin(
                providers["auth0"]["signinUrl"], csrf["csrfToken"])
            state = self._request_authorize(sigin["url"])
            state = self._request_login_identifier(state)
            state = self._request_login_identifier_post(state, username)
            state = self._request_login_password(state)
            state = self._request_login_password_post(state, username, password)
            self._request_authorize_access_token(state)
            random_sleep_time(1, 2)
            return self.get_session()
        except HTTPTLSError as err:
            raise ChatgptError("Login error. Try again or use interceptor.js as explained in the documentation.",
                               ChatgptErrorCodes.LOGIN_ERROR) from err
