import { useEffect, useState } from "react";


const conversations = {

  "1": [

    {
      id: 1,
      role: "user",
      avatar: "RS",
      content:
        "How does hostel re-allotment work after 2nd year, and can I request a specific room?"
    },

    {
      id: 2,
      role: "assistant",
      avatar: "AI",
      content:
        "Re-allotment for returning students happens through the Dean of Student Welfare's online portal, usually in the last week of June. Seniority decides allotment order within the hostel block.",

      citations:[
        "Hostel Manual v2026 §3.2",
        "DoSW Circular 44/26"
      ]

    }

  ],


  "4": [

    {
      id:3,
      role:"user",
      avatar:"RS",
      content:
        "What is the last date to apply for mess rebate?"
    },

    {
      id:4,
      role:"assistant",
      avatar:"AI",
      content:
        "Mess rebate applications should be submitted before the deadline mentioned in the latest mess circular.",

      citations:[
        "Mess Circular 2026"
      ]

    }

  ]

};



export default function useChat(conversationId){


  const [messages,setMessages] = useState(
    conversations[conversationId] || []
  );


  const [isTyping,setIsTyping] = useState(false);



  useEffect(()=>{


    setMessages(
      conversations[conversationId] || []
    );


  },[conversationId]);





  const sendMessage = (text)=>{


    const userMessage = {

      id:Date.now(),

      role:"user",

      avatar:"RS",

      content:text

    };



    setMessages((prev)=>[

      ...prev,

      userMessage

    ]);



    setIsTyping(true);



    // temporary AI response

    setTimeout(()=>{


      setIsTyping(false);



      setMessages((prev)=>[

        ...prev,

        {

          id:Date.now(),

          role:"assistant",

          avatar:"AI",

          content:
            "This is a demo response. WebSocket backend integration will replace this.",

          citations:[
            "MNIT Official Documents"
          ]

        }

      ]);



    },1500);


  };




  return {

    messages,

    sendMessage,

    isTyping

  };


}