export const createChatSocket = (
  conversationId,
  token,
  onMessage,
  onClose
)=>{


  const socket = new WebSocket(

    `ws://localhost:8000/chat/${conversationId}?token=${token}`

  );



  socket.onopen = ()=>{

    console.log(
      "WebSocket connected"
    );

  };



  socket.onmessage = (event)=>{


    const data = JSON.parse(
      event.data
    );


    onMessage(data);


  };



  socket.onclose = ()=>{


    console.log(
      "WebSocket disconnected"
    );


    if(onClose){
      onClose();
    }


  };



  socket.onerror = (error)=>{

    console.error(
      "WebSocket error",
      error
    );

  };



  return socket;

};