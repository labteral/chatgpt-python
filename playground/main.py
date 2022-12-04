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
