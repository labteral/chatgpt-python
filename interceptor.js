const textareas = document.getElementsByTagName('textarea');
const lastTextarea = textareas[textareas.length - 1];

let buttons = document.getElementsByTagName('button');
buttons = Array.prototype.slice.call(buttons);
const lastButton = buttons[buttons.length - 1];

lastTextarea.value = 'Hello'
lastButton.click();

var interval = setInterval(function() {
  if (lastButton.disabled === false) {
    clearInterval(interval);
    lastTextarea.value = "Let's start"
    lastButton.click();
  }
}, 100);

function fetchInterceptor(fetch) {
  return function(...args) {
    const body = JSON.parse(args[1]?.body);
    const headers = args[1]?.headers;
    
    const accessToken = headers?.Authorization.split('Bearer')[1].trim()
    const conversationId = body?.conversation_id
    const parentMessageId = body?.parent_message_id

    if (accessToken && conversationId && parentMessageId) {
      const config = {
        access_token: accessToken,
        conversation_id: body.conversation_id,
        parent_message_id: body.parent_message_id,
      };
      console.log(JSON.stringify(config));
    }

    return fetch(...args);
  };
}
window.fetch = fetchInterceptor(window.fetch);
