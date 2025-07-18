from flask import Blueprint, request, jsonify, render_template, send_from_directory
import os
import sys 


MODULES_PATH = "Modules/"

sys.path.append(MODULES_PATH)

from Wikipedia_Rag import WikipediaRAG











Api_Webapp_Rag_Using_Page = Blueprint('Api_Webapp_Rag_Using_Page', __name__, url_prefix='/Rag_Using_Page')

WIKIPEDIA_DATA_PATH = os.path.join("Data")



@Api_Webapp_Rag_Using_Page.route('/')
def Home_Page_Rag_Using_Page():
    return render_template('Rag_Using_Page.html')



Use_Multi_Query = False
Use_Rag_Fusion = False
API_URL_Ollama = "http://localhost:11434/api/generate"

Ollama_Model_Name = "llama3.1:8b" 



MyRAG = WikipediaRAG(
    Data_Folder_Path="Data",
    Embedding_Model= "BAAI/bge-base-en-v1.5",
    Batch_Size_Embedding=16,
    Api_Url=API_URL_Ollama, 
    Model_Name=Ollama_Model_Name,
    Use_Multi_Query=Use_Multi_Query,
    Use_Rag_Fusion=Use_Rag_Fusion,
    Nb_Chunks_To_Retrieve = 5,
    Nb_Multi_Querries=5
)

@Api_Webapp_Rag_Using_Page.route('/set_rag_mode', methods=["GET", "POST"])
def Define_Rag_Mode():
    global Use_Multi_Query
    global Use_Rag_Fusion
    global MyRAG
    if request.method == "POST":
        data = request.json
        Use_Multi_Query = bool(data.get("use_multi_query", False))
        Use_Rag_Fusion = bool(data.get("use_rag_fusion", False))
        nb_chunks_to_retrieve = int(data.get("nb_chunks_to_retrieve", 10))
        nb_multi_queries = int(data.get("nb_multi_queries", 3))

        print(f"RAG modes set - Multi-Query: {Use_Multi_Query}, RAG Fusion: {Use_Rag_Fusion}, Num nb_chunks_to_retrieve: {nb_chunks_to_retrieve}, Nb Multi Queries: {nb_multi_queries}")

        MyRAG.Use_Multi_Query = Use_Multi_Query
        MyRAG.Use_Rag_Fusion = Use_Rag_Fusion
        MyRAG.Nb_Chunks_To_Retrieve = nb_chunks_to_retrieve
        MyRAG.Nb_Multi_Queries = nb_multi_queries

        return jsonify({
            "status": "success",
            "message": "Les modes RAG ont été définis avec succès.",
            "use_multi_query": Use_Multi_Query,
            "use_rag_fusion": Use_Rag_Fusion,
            "nb_chunks_to_retrieve": nb_chunks_to_retrieve,
            "nb_multi_queries": nb_multi_queries
        })
    else:
        # GET method: return current settings
        nb_chunks_to_retrieve = getattr(MyRAG, "Nb_Chunks_To_Retrieve", 10)
        nb_multi_queries = getattr(MyRAG, "Nb_Multi_Queries", 3)
        return jsonify({
            "use_multi_query": Use_Multi_Query,
            "use_rag_fusion": Use_Rag_Fusion,
            "nb_chunks_to_retrieve": nb_chunks_to_retrieve,
            "nb_multi_queries": nb_multi_queries
        })




PATH_SAVING_ANNOY_INDEX = "Annoy_Index/wikipedia_index.ann"
PATH_SAVING_CHUNKS = "Chunks/chunks.pickle"
EMBEDDING_SIZE = 768  # Adjust this based on your embedding model
Annoy_Index=None
Chunks = None
Text_Of_Chunks = None
Relevant_Chunks = None
@Api_Webapp_Rag_Using_Page.route("/Load_Annoy_Index", methods=["GET"])
def Load_Annoy_Index_Api():
    global Annoy_Index
    print("================== Load Annoy Index =====================")
    try:
        Annoy_Index = MyRAG.Load_Annoy_Index(PATH_SAVING_ANNOY_INDEX, EMBEDDING_SIZE)
        return jsonify({"status": "success", "message": "Annoy index loaded successfully."})
    except Exception as e:
        print(f"Error loading Annoy index: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    


@Api_Webapp_Rag_Using_Page.route("Load_Chunks",methods = ["GET"])
def Load_Chunks_Api():
    global Chunks
    global Text_Of_Chunks
    print("================== Load Chunks =====================")
    try:
        Chunks = MyRAG.Load_Chunks(Saving_Path=PATH_SAVING_CHUNKS)
        Text_Of_Chunks = MyRAG.Access_Text_Of_Chunks(Chunks=Chunks)

        return jsonify({"status": "success", "message": "Chunks loaded successfully and texts extracted.", 
                        "num_chunks": len(Chunks), 
                        "num_texts": len(Text_Of_Chunks)}), 200
    except Exception as e:
        print(f"Error loading chunks: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    





# @Api_Webapp_Rag_Using_Page.route("Retrieve_Chunks", methods=["POST"])
# def Retrieve_Chunks_Api():
#     global Annoy_Index
#     global Chunks
#     try:
#         data = request.json
#         query = data.get("query", "")
#         if not query:
#             return jsonify({"status": "error", "message": "Query is required."}), 400

#         relevant_chunks = MyRAG.Retrieve_Chunks(Annoy_Index=Annoy_Index, Query=query, Chunks=Text_Of_Chunks, Num_Results=10)

#         return jsonify({"status": "success", "data": relevant_chunks})
#     except Exception as e:
#         print(f"Error retrieving chunks: {e}")
#         return jsonify({"status": "error", "message": str(e)}), 500
#         return jsonify({"status": "success", "data": chunks})
#     except Exception as e:
#         print(f"Error retrieving chunks: {e}")
#         return jsonify({"status": "error", "message": str(e)}), 500


# @Api_Webapp_Rag_Using_Page.route('Generate_Response', methods=['POST'])
# def Generate_Response_Api():
#     print("================== Generate Response =====================")
#     try:
#         data = request.json
#         query = data.get("query", "")
#         if not query:
#             return jsonify({"status": "error", "message": "Query is required."}), 400
#         else:
#             print(f"Query received: {query}")
#         response = MyRAG.Generate_Response(Query=query,Chunk_Sources=Chunks)
#         return jsonify({"status": "success", "response": response})
#     except Exception as e:
#         print(f"Error generating response: {e}")
#         return jsonify({"status": "error", "message": str(e)}), 500
    

@Api_Webapp_Rag_Using_Page.route("Retrieve_And_Generate", methods=["POST"])
def Retrieve_And_Generate_Api():
    global Annoy_Index
    global Chunks
    global Text_Of_Chunks
    global Relevant_Chunks
    try:
        print("================== Retrieve And Generate =====================")
        data = request.json
        query = data.get("query", "")
        print(f"Received query: {query}")
        if not query:
            print("No query provided.")
            return jsonify({"status": "error", "message": "Query is required."}), 400

        # Retrieve relevant chunks
        print("Retrieving relevant chunks...")
        Relevant_Chunks = MyRAG.Retrieve_Chunks(
            Annoy_Index=Annoy_Index,
            Query=query,
            Chunks=Text_Of_Chunks,
            Num_Results=10
        )
        print(f"Retrieved {len(Relevant_Chunks)} relevant chunks.")

        # Generate response using the retrieved chunks
        print("Generating response...")
        response = MyRAG.Generate_Response(
            Query=query,
            Chunk_Sources=Relevant_Chunks
        )
        print("Response generated.")

        return jsonify({
            "status": "success",
            "relevant_chunks": Relevant_Chunks,
            "response": response
        })
    except Exception as e:
        print(f"Error in Retrieve_And_Generate: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    


    # Pour récupérer le texte d'un chunk i
@Api_Webapp_Rag_Using_Page.route("Access_Text_Of_Chunk", methods=["POST"])
def Access_Text_Of_Chunk_Api():
    global Relevant_Chunks

    try:
        data = request.json
        chunk_index = data.get("chunk_index", -1)
        if chunk_index == -1:
            return jsonify({"status": "error", "message": "Chunk index is required."}), 400

        text = Relevant_Chunks[chunk_index] if 0 <= chunk_index < len(Relevant_Chunks) else ""
        return jsonify({"status": "success", "text": text})
    except Exception as e:
        print(f"Error accessing chunk text: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500