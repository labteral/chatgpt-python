<h1 align="center">ChatGPT Python SDK</h1>

<br />
<p align="center">
    <a href="https://github.com/labteral/chatgpt-python/issues"><img alt="PyPi" src="https://img.shields.io/github/issues/labteral/chatgpt-python.svg?style=flat-square"></a>
    <a href="https://pypi.python.org/pypi/chatgpt/"><img alt="PyPi" src="https://img.shields.io/pypi/v/chatgpt.svg?style=flat-square"></a>
    <a href="https://github.com/labteral/chatgpt-python/blob/master/LICENSE"><img alt="License" src="https://img.shields.io/github/license/labteral/chatgpt-python.svg?style=flat-square"></a>
</p>


## Install or update
```bash
pip install -U chatgpt
```


## Create a file with your credentials
> :warning: &nbsp; Please, update the library. Note the change in the config file.

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

    //Timeout for requests made.
    "timeout":300,
    
    //Cache for saving the cookies and the state of the session.
    "cache_file_path":"./path_and_filename"
}
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

### SDK
```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from chatgpt import Conversation

conversation = Conversation()

# Python generator to stream the message in chunks.
# the chunk give you a new part of the final message.
for chunk in conversation.stream("We are going to start a conversation. I will speak English and you will speak Portuguese."):
    # print chunk without line break
    print(chunk, end="")
    # flush terminal output
    sys.stdout.flush()

# this conversation chat instead is going to wait until the response is completely received.
print(conversation.chat("What's the color of the sky?"))

# The AI will forget it was speaking Portuguese
conversation.reset()
print(conversation.chat("What's the color of the sun?"))

```
