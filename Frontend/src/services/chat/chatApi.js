import api from "../api/api";


export const getChatHistory = async(conversationId)=>{

  const response = await api.get(
    `/chat/${conversationId}`
  );

  return response.data;

};



export const sendChatMessage = async(
  conversationId,
  message
)=>{

  const response = await api.post(

    `/chat/${conversationId}`,

    {
      message
    }

  );


  return response.data;

};