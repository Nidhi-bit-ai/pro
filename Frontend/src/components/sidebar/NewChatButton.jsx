import { Plus } from "lucide-react";

export default function NewChatButton() {
  return (
    <button className="new-chat-btn">
      <Plus size={15} strokeWidth={2} />
      <span>New chat</span>
    </button>
  );
}