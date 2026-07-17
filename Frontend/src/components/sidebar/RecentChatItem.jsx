import { useNavigate } from "react-router-dom";


export default function RecentChatItem({

  id,

  title,

  time,

  active = false,

}) {

  const navigate = useNavigate();


  return (

    <button

      className={
        active
          ? "history-item active"
          : "history-item"
      }

      onClick={() => navigate(`/chat/${id}`)}

    >

      {title}


      <span className="history-time">

        {time}

      </span>


    </button>

  );

}