import { useParams } from "react-router-dom";

import ChatHeader from "../../components/chat/ChatHeader";
import Thread from "../../components/chat/Thread";
import Composer from "../../components/chat/Composer";

import useChat from "../../hooks/useChat";


export default function Chat(){


  const { id } = useParams();


  const {
    messages,
    sendMessage,
    isTyping

  } = useChat(id);



  return (

    <main className="chat-page">


      <ChatHeader />


      <Thread

        messages={messages}

        isTyping={isTyping}

      />


      <Composer

        onSend={sendMessage}

      />


    </main>

  );

}