import requests


def Define_Default_Resource_Template():
    return """You are an AI assistant that answers questions based on provided documents.

    Question: {question}

    Documents:
    {documents}

    Please provide a concise and accurate answer based only on the information in the documents, and answer preciesely the question that is given (only the question).
    If the answer is not present in the provided documents, reply with "The answer is not in the documents.
    """


def Generate_Response_Straight(Querry, Chunk_Sources, Resource_Template=Define_Default_Resource_Template(), API_URL="http://localhost:11434/api/generate", Model_Name="llama3"):
    print("Enterign Generation")
    Prompt_Text = Resource_Template.format(
        question=Querry,
        documents="\n".join(Chunk_Sources)
    )
    Request_Payload = {
        "model": Model_Name,
        "prompt": Prompt_Text,
        "stream": False
    }
    API_Response = requests.post(API_URL, json=Request_Payload)


    print(f"API OLLAMA Response Status Code: {API_Response.status_code}")
    if API_Response.status_code != 200:
        raise Exception(f"API request failed with status code {API_Response.status_code}: {API_Response.text}")

    Response_Data = API_Response.json()
    
    # Pour Ollama, la clé est "response"
    if "response" not in Response_Data:
        raise Exception("API response does not contain 'response' key.")
    
    Response_Text = Response_Data["response"].strip()
    return Response_Text



# Multi-Querry


def Generate_Response_Multi_Querry(Querry, Chunk_Sources, Resource_Template=Define_Default_Resource_Template(), API_URL="http://localhost:11434/api/generate", Model_Name="llama3"):
    print("Entering Multi-Query Generation")


    return Generate_Response_Straight(Querry, Chunk_Sources, Resource_Template, API_URL, Model_Name)

def Generate_Response_Rag_Fusion(Querry, Chunk_Sources, Resource_Template=Define_Default_Resource_Template(), API_URL="http://localhost:11434/api/generate", Model_Name="llama3"):
    print("Entering Multi-Query Generation")


    return Generate_Response_Straight(Querry, Chunk_Sources, Resource_Template, API_URL, Model_Name)


if __name__ == "__main__":

    # Example usage
    print("Generating response for the query...")
    query = "What liquid boils at almost 100 degrees Celsius?"
    chunks = [
        "Water boils at 100 degrees Celsius.",
        "The capital of France is Paris.",
        "The Eiffel Tower is located in Paris."
        "The capital of Morocco is near the Atlantic Ocean.",
        "The capital of Morocco name starts with 'R' and ends with 'bat'.",
    ]
    response = Generate_Response_Straight(query, chunks,Model_Name="llama3.1:8b")
    print(response)  # Expected output: "The capital of France is Paris."

