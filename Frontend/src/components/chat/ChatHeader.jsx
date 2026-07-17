import { useParams } from "react-router-dom";


const chatTitles = {

  "1": "Hostel re-allotment process",

  "4": "Mess rebate deadline"

};



export default function ChatHeader() {


  const { id } = useParams();


  return (

    <div className="chat-header">


      <div className="chat-title">

        {chatTitles[id] || "New Conversation"}

      </div>



      <div className="scope-pill">

        <span className="dot"></span>

        Scope: All MNIT sources

      </div>


    </div>

  );

}