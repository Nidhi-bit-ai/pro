import { ArrowUp, Paperclip } from "lucide-react";

export default function AskBox() {
  return (
    <div className="ask-frame">
      <div className="ask-inner">
        <input
          type="text"
          placeholder="What's the last date to apply for mess rebate?"
        />

        <button
          className="attach-document"
          aria-label="Attach document"
        >
          <Paperclip size={15} />
        </button>

        <button
          className="ask-send"
          aria-label="Send"
        >
          <ArrowUp size={17} />
        </button>
      </div>
    </div>
  );
}