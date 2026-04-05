def query_rag(query: str, history=None):
    # TEMP MOCK RESPONSE (no RAG server needed)

    return {
        "answer": f"Mock answer for: '{query}'"
    }


#import requests

#RAG_SERVER_URL = "http://127.0.0.1:9000"  # change if needed


#def query_rag(query: str):
 #   try:
  #      response = requests.post(
   #         f"{RAG_SERVER_URL}/query",
     #       json={"query": query},
      #      timeout=30
      #  )

      #  if response.status_code == 200:
      #      return response.json()

      #  return {"answer": "Error from RAG server"}

    #except Exception as e:
      #  return {"answer": f"RAG connection error: {str(e)}"}