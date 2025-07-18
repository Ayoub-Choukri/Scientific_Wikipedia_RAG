import requests
import re




def Define_Default_Multi_Querry_Template(Nb_Multi_Querries = 5):
    

    Template = """
You are an AI language model assistant. Your task is to generate 
{Nb_Multi_Querries} different rephrasings of the given user question, strictly keeping the original meaning and not adding or removing any information. Do NOT broaden, narrow, or change the intent of the question. Only generate alternative phrasings or perspectives of the same question, without providing answers.

Each question must be wrapped between <SOQ> and <EOQ>, and output only the questions, nothing else.

Original Question: {Question}

# Example:
# If the original question is: What is the capital of France? And you are asked to generate 2 different versions of this question, your output should be:
# <SOQ>Which city serves as the capital of France?<EOQ>
# <SOQ>What is the main city of France?<EOQ>
"""

# Example:
# If the original question is: What is the capital of France? And you are asked to generate 5 different versions of this question, your output should be:
# Then your output should be:
# <SOQ>Which city serves as the capital of France?<EOQ>
# <SOQ>What is the main city of France?<EOQ>
# <SOQ>Can you tell me the capital city of France?<EOQ>
# <SOQ>Which city is the administrative center of France?<EOQ>
# <SOQ>What city is known as the capital of France?<EOQ>    

    return Template






def Generate_Multi_Querries(Question, Nb_Multi_Querries=5 , API_OLLAMA_URL = "http://localhost:11434/api/generate", Ollama_Model_Name="llama3"):
    """
    Generate multiple versions of the user question to retrieve relevant documents from a vector database.
    """
    Resource_Template = Define_Default_Multi_Querry_Template(Nb_Multi_Querries)
    Prompt_Text = Resource_Template.format(
        Nb_Multi_Querries=Nb_Multi_Querries,
        Question=Question
    )
    
    print(f"Prompt Text: {Prompt_Text}")
    Request_Payload = {
        "model": Ollama_Model_Name,
        "prompt": Prompt_Text,
        "stream": False
    }
        
    print(API_OLLAMA_URL)
    API_Response = requests.post(API_OLLAMA_URL, json=Request_Payload)

    print(f"API OLLAMA Response Status Code: {API_Response.status_code}")
    if API_Response.status_code != 200:
        raise Exception(f"API request failed with status code {API_Response.status_code}: {API_Response.text}")

    Response_Data = API_Response.json()
    
    # Pour Ollama, la clé est "response"
    if "response" not in Response_Data:
        raise Exception("API response does not contain 'response' key.")
    
    Response_Text = Response_Data["response"].strip()
    
    # Split the response into multiple queries
    # Extract questions wrapped between <SOQ> and <EOQ>

    print(f"{Response_Text}")
    Multi_Queries = re.findall(r"<SOQ>(.*?)<EOQ>", Response_Text, re.DOTALL)
    Multi_Queries = [q.strip() for q in Multi_Queries if q.strip()]
    
    return Multi_Queries





if __name__ == "__main__":
    # Example usage
    print("Generating multiple queries for the question...")
    question = "What is the name of the city that is calles pink city?"
    multi_queries = Generate_Multi_Querries(question, Nb_Multi_Querries=3, Ollama_Model_Name="llama3.1:8b")
    print("Generated Multi-Queries:")
    print(len(multi_queries))
    for idx, q in enumerate(multi_queries):
        print(f"{idx + 1}: {q}")
    # Expected output: Multiple variations of the question "What liquid boils at 100 degrees Celsius
