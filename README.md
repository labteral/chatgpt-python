## Get the credentials
1. Login into https://chat.openai.com/chat with your browser
2. Paste the content of [interceptor.js](/chatgpt/interceptor.js) in the browser console
3. Store the JSON in a file called `config.json`


## Usage
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


