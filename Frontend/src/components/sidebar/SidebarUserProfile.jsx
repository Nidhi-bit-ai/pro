export default function SidebarUserProfile() {
  const user = {
    initials: "NG",
    name: "Nidhi Gurjar",
    role: "B.Tech AIDE · 3rd Year",
  };

  return (
    <div className="sidebar-footer">
      <div className="avatar">
        {user.initials}
      </div>

      <div className="user-meta">
        <div>{user.name}</div>

        <div className="role">
          {user.role}
        </div>
      </div>
    </div>
  );
}