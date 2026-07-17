import RecentChatItem from "./RecentChatItem";

const chats = [
  {
    id: 1,
    title: "Hostel re-allotment process",
    time: "Today · 10:42",
    active: true,
  },
  {
    id: 2,
    title: "B.Tech backlog exam rules",
    time: "Today · 09:15",
  },
  {
    id: 3,
    title: "Summer internship NOC format",
    time: "Yesterday",
  },
  {
    id: 4,
    title: "Mess rebate application",
    time: "Yesterday",
  },
  {
    id: 5,
    title: "Library fine waiver policy",
    time: "5 days ago",
  },
];

export default function RecentChats() {
  return (
    <>
      <div className="nav-section-label">
        Recent
      </div>

      <div className="history-list">
        {chats.map((chat) => (
          <RecentChatItem
            key={chat.id}
            {...chat}
          />
        ))}
      </div>
    </>
  );
}