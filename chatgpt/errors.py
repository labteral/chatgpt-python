from enum import Enum


class ChatgptErrorCodes(Enum):
    """
    Error codes returned by the API.
    """
    INVALID_ACCESS_TOKEN = "invalid_access_token"
    CHATGPT_API_ERROR = "chat_gpt_api_error"
    CONFIG_FILE_ERROR = "config_file_error"
    UNKNOWN_ERROR = "unknown_error"
    LOGIN_ERROR = "login_error"
    TIMEOUT_ERROR = "timeout_error"
    CONNECTION_ERROR = "connection_error"

class ChatgptError(Exception):
    """
    Base class for exceptions raised by the Chatgpt API.
    """
    def __init__(self, message, code=ChatgptErrorCodes.UNKNOWN_ERROR):
        super().__init__(message)
        self.code = code
        self.message = message
