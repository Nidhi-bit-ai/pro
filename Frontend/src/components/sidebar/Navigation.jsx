import {
  House,
  MessageSquare,
  BookOpen,
} from "lucide-react";

import NavItem from "./NavItem";

export default function Navigation() {
  return (
    <>
      <NavItem
        to="/"
        icon={House}
        label="Home"
        end
      />

      <NavItem
        to="/chat"
        icon={MessageSquare}
        label="Chat"
      />

      <NavItem
        to="/documents"
        icon={BookOpen}
        label="Sources Library"
      />
    </>
  );
}