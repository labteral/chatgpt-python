<h1 align="center">ChatGPT Python SDK</h1>
<p align="center">
    Library that allows developers to easily integrate the ChatGPT into their Python projects.
    <br />
    <br />
</p>
<p align="center">
    <a href="https://github.com/labteral/chatgpt-python/issues"><img alt="PyPi" src="https://img.shields.io/github/issues/labteral/chatgpt-python.svg?style=flat-square"></a>
    <a href="https://pypi.python.org/pypi/chatgpt/"><img alt="PyPi" src="https://img.shields.io/pypi/v/chatgpt.svg?style=flat-square"></a>
    <a href="https://github.com/labteral/chatgpt-python/blob/master/LICENSE"><img alt="License" src="https://img.shields.io/github/license/labteral/chatgpt-python.svg?style=flat-square"></a>
</p>


## Install or update
```bash
pip install -U chatgpt
```

## Config
### Create a file with your credentials

Create the file `config.json` in your working directory: 
```json
{
    "email": "email@example.org",
    "password": "xxx",
}
```

### With proxy
```json
{
    "email": "email@example.org",
    "password": "xxx",
    "proxy": "socks5://user:pass@host:port"
}
```

### With other parameters
```json
{
    "email": "email@example.org",
    "password": "xxx",

    // Timeout per request.
    "timeout":300,
    
    // Cache for saving the cookies and the state of the session.
    "cache_file_path":"/path/filename",

    // Time for refresh the access token.
    "access_token_seconds_to_expire":1800
}
```

## Environment variable
You can specify the default configuration folder for chatgpt by setting the `CHATGPT_HOME` environment variable to the desired directory path.

```bash
export CHATGPT_HOME="/home/$USER/.config/chatgpt"
```


## Usage
### CLI
You can launch the CLI with:
```bash
chatgpt
```
or
```bash
python -m chatgpt
```

These are the available commands:
- `reset`: forget the context of the current conversation.
- `clear`: clear the terminal.
- `exit`: exit the CLI.


<br/>

### SDK
```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from chatgpt import Conversation

conversation = Conversation()

# Stream the message as it arrives.
for chunk in conversation.stream("We are going to start a conversation. I will speak English and you will speak Portuguese."):
    print(chunk, end="")
    sys.stdout.flush()

# Wait until the message is fully received.
print(conversation.chat("What's the color of the sky?"))

# The AI will forget it was speaking Portuguese
conversation.reset()
print(conversation.chat("What's the color of the sun?"))

```
> it is recommended to use *stream* instead of *chat*.
#### **Exceptions**:

```python
from chatgpt import ChatgptError, ChatgptErrorCodes

try:

    for chunk in conversation.stream("Hello, world!"):
        print(chunk, end="")
        sys.stdout.flush()

except ChatgptError as chatgpt_error:

    message = chatgpt_error.message
    code = chatgpt_error.code

    if code == ChatgptErrorCodes.INVALID_ACCESS_TOKEN:
        print("Invalid token")

```


#### **Chatgpt Error codes (Generated with chatgpt):**

- `INVALID_ACCESS_TOKEN`: This error code indicates that the access token provided to the chatbot's API is not valid or has expired.
- `CHATGPT_API_ERROR`: This error code indicates that an error has occurred while making a request to the chatbot's API.
- `CONFIG_FILE_ERROR`: This error code indicates that there is a problem with the configuration file for the chatbot.
- `UNKNOWN_ERROR`: This error code is used when the cause of the error is unknown or cannot be determined.
- `LOGIN_ERROR`: This error code indicates that there was a problem with the login process, such as an incorrect username or password.
- `TIMEOUT_ERROR`: This error code indicates that a request to the chatbot's API has timed out.
- `CONNECTION_ERROR`: This error code indicates that there is a problem with the connection to the chatbot's API.
