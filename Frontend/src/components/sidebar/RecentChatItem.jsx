export default function RecentChatItem({
  title,
  time,
  active = false,
}) {
  return (
    <button
      className={
        active
          ? "history-item active"
          : "history-item"
      }
    >
      {title}

      <span className="history-time">
        {time}
      </span>
    </button>
  );
}