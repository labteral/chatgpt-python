<p align="center">
    <a href="https://pepy.tech/project/chatgpt/"><img alt="Downloads" src="https://img.shields.io/badge/dynamic/json?style=flat-square&maxAge=3600&label=downloads&query=$.total_downloads&url=https://api.pepy.tech/api/projects/chatgpt-python"></a>
    <a href="https://pypi.python.org/pypi/chatgpt/"><img alt="PyPi" src="https://img.shields.io/pypi/v/chatgpt-python.svg?style=flat-square"></a>
    <a href="https://github.com/labteral/chatgpt-python/blob/master/LICENSE"><img alt="License" src="https://img.shields.io/github/license/labteral/chatgpt-python.svg?style=flat-square"></a>
</p>

<h3 align="center">
    <b>ChatGPT Python SDK</b>
</h3>

<p align="center">
    <a href="https://www.buymeacoffee.com/brunneis" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="35px"></a>
</p>

## Install
```bash
pip install -U chatgpt
```

## Get the credentials
1. Login into https://chat.openai.com/chat with your browser
2. Paste the content of [interceptor.js](/chatgpt/interceptor.js) in the browser console
3. Store the JSON in a file called `config.json`


## Usage
### Interactive chat
```bash
chatgpt
```
or
```bash
python -m chatgpt
```
### SDK
```python
from chatgpt import Conversation

conversation = Conversation()
print(
    conversation.chat(
        "We are going to start a conversation. "
        "I will speak English and you will speak Portuguese."
    )
)
print(conversation.chat("What's the color of the sky?"))

# The AI will forget it was speaking Portuguese
conversation.reset()
print(conversation.chat("What's the color of the sun?"))
```


