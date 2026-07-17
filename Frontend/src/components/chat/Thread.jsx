import { useEffect, useRef } from "react";
import Message from "./Message";
import TypingIndicator from "./TypingIndicator";

export default function Thread({

  messages,

  isTyping = false

}) {

  const threadRef = useRef(null);

  useEffect(() => {

    if (!threadRef.current) return;

    threadRef.current.scrollTop =
      threadRef.current.scrollHeight;

  }, [messages, isTyping]);

  return (

    <div
      ref={threadRef}
      className="thread"
    >

      {messages.map((message) => (

        <Message
          key={message.id}
          role={message.role}
          avatar={message.avatar}
          citations={message.citations}
        >

          {message.content}

        </Message>

      ))}

      {isTyping && <TypingIndicator />}

    </div>

  );

}