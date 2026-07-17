import { NavLink } from "react-router-dom";

import {
  Plus,
  Home,
  MessageSquare,
  BookOpen
} from "lucide-react";


const recentChats = [
  "Hostel re-allotment process",
  "B.Tech backlog exam rules",
  "Summer internship NOC format",
  "Mess rebate application",
  "Scholarship renewal docs",
  "Library fine waiver policy"
];


export default function Sidebar() {

  return (

    <aside className="sidebar">


      {/* Brand */}

      <div className="brand">

        <svg
          width="26"
          height="26"
          viewBox="0 0 26 26"
          fill="none"
        >

          <path
            d="M13 1L23 7V19L13 25L3 19V7L13 1Z"
            stroke="#15c1af"
            strokeWidth="1.4"
          />

          <path
            d="M13 7L18 10V16L13 19L8 16V10L13 7Z"
            stroke="#f0a838"
            strokeWidth="1.4"
          />

        </svg>


        <div className="brand-name">
          ask<span>MNIT</span>
        </div>


      </div>



      {/* New Chat */}

      <button className="new-chat-btn">

        <Plus size={15} />

        New chat

      </button>



      {/* Navigation */}

      <nav>


        <NavLink
          to="/"
          className={({ isActive }) =>
            isActive
              ? "nav-item active"
              : "nav-item"
          }
        >

          <Home size={16} />

          Home

        </NavLink>



        <NavLink
          to="/chat/new"
          className={({ isActive }) =>
            isActive
              ? "nav-item active"
              : "nav-item"
          }
        >

          <MessageSquare size={16} />

          Chat

        </NavLink>



        <NavLink
          to="/documents"
          className={({ isActive }) =>
            isActive
              ? "nav-item active"
              : "nav-item"
          }
        >

          <BookOpen size={16} />

          Sources Library

        </NavLink>


      </nav>



      {/* Recent */}

      <div className="nav-section-label">
        Recent
      </div>



      <div className="history-list">

        {
          recentChats.map((chat, index) => (

            <NavLink
              key={index}
              to={`/chat/${index + 1}`}
              className="history-item"
            >

              {chat}


              <span className="history-time">

                {
                  index < 2
                    ? "Today"
                    : index < 4
                      ? "Yesterday"
                      : "5 days ago"
                }

              </span>


            </NavLink>

          ))
        }


      </div>



      {/* Profile */}

      <div className="sidebar-footer">


        <div className="avatar">
          RS
        </div>


        <div className="user-meta">

          Riya Sharma


          <div className="role">
            B.Tech AIDE · 4th yr
          </div>


        </div>


      </div>


    </aside>

  );

}