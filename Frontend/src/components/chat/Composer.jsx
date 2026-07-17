import { useRef, useState } from "react";
import { Paperclip, ArrowUp } from "lucide-react";

export default function Composer({ onSend = () => {} }) {

  const [message, setMessage] = useState("");

  const textareaRef = useRef(null);

  const autoGrow = () => {

    const textarea = textareaRef.current;

    if (!textarea) return;

    textarea.style.height = "0px";

    textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;

  };

  const handleChange = (e) => {

    setMessage(e.target.value);

    autoGrow();

  };

  const sendMessage = () => {

    const text = message.trim();

    if (!text) return;

    onSend(text);

    setMessage("");

    if (textareaRef.current) {
      textareaRef.current.style.height = "22px";
    }

  };

  const handleKeyDown = (e) => {

    if (e.key === "Enter" && !e.shiftKey) {

      e.preventDefault();

      sendMessage();

    }

  };

  return (

    <div className="composer">

      <div className="composer-frame">

        <textarea

          ref={textareaRef}

          rows={1}

          value={message}

          placeholder="Ask about MNIT..."

          onChange={handleChange}

          onKeyDown={handleKeyDown}

        />



        <div className="composer-actions">

          <button

            className="icon-btn"

            type="button"

            title="Attach a document"

          >

            <Paperclip size={16} />

          </button>



          <button

            className="icon-btn send-btn"

            type="button"

            disabled={!message.trim()}

            onClick={sendMessage}

            title="Send"

          >

            <ArrowUp size={15} />

          </button>

        </div>

      </div>



      <div className="composer-hint">

        Answers are generated from official MNIT documents.
        Verify critical deadlines with the concerned office.

      </div>

    </div>

  );

}