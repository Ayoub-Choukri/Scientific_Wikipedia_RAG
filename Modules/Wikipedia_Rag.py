from Chunking import *
from Embeddings_Chunks import *
from Retrieval import *
from Generation import *
from Multi_Querry import *



class WikipediaRAG:
    def __init__(self, Data_Folder_Path, Embedding_Model="BAAI/bge-small-en",Batch_Size_Embedding=16, Search_K = 500,Api_Url="http://localhost:11434/api/generate", Model_Name="llama3",Use_Multi_Query=False, Use_Rag_Fusion = False,Nb_Chunks_To_Retrieve = 5, Nb_Multi_Querries=5):
        self.Data_Folder_Path = Data_Folder_Path
        self.Embedding_Model = Embedding_Model
        self.Api_Url = Api_Url
        self.Model_Name = Model_Name
        self.Batch_Size_Embedding = Batch_Size_Embedding
        self.Search_K = Search_K  # Number of neighbors to search for in Annoy index
        self.Use_Multi_Query = Use_Multi_Query
        self.Use_Rag_Fusion = Use_Rag_Fusion
        self.Nb_Multi_Querries = Nb_Multi_Querries
        self.Nb_Chunks_To_Retrieve = Nb_Chunks_To_Retrieve
    def Chunk_Articles(self, Chunk_Size=1000, Chunk_Overlap=200):
        """
        Charge les articles Wikipedia, les divise en chunks.
        """
        Text_Splitter = Create_Text_Splitter(Chunk_Size=Chunk_Size, Chunk_Overlap=Chunk_Overlap)
        Chunks = Chunk_Text_Of_Folder(self.Data_Folder_Path, Text_Splitter, Extension=".txt")
        return Chunks


    def Save_Chunks(self, Chunks, Saving_Path):
        """
        Sauvegarde les chunks dans un fichier pickle.
        """
        Save_Chunks_To_Pickle(Chunks, Saving_Path)

    def Load_Chunks(self, Saving_Path):
        """
        Charge les chunks à partir d'un fichier pickle.
        """
        Chunks = Load_Chunks_From_Pickle(Saving_Path)
        return Chunks
    
    def Access_Text_Of_Chunks(self, Chunks):
        """
        Retourne une liste des textes de chaque chunk dans Chunks, avec une barre de progression.
        """
        Texts_Of_Chunks = Acces_Text_Of_Chunks(Chunks)
        return Texts_Of_Chunks
    
    
    def Embed_Chunks(self, Chunks):
        """
        Crée des embeddings pour les chunks de texte.
        """
        Embedder = Create_Embedder(Embedding_Model=self.Embedding_Model)
        Embeddings = Embed_Chunks(Chunks, Embedder, batch_size=self.Batch_Size_Embedding)
        return Embeddings
    
    def Save_Embeddings_Of_Chunks(self, Embeddings, Saving_Path):
        """
        Sauvegarde les embeddings dans un fichier.
        """
        Save_Embeddings(Embeddings, Saving_Path)


    def Load_Embeddings_Of_Chunks(self, Saving_Path):
        """
        Charge les embeddings à partir d'un fichier.
        """
        Embeddings = Load_Embeddings(Saving_Path)
        return Embeddings
    


    def Create_Annoy_Index(self, Embeddings, Num_Trees=10, File_Path="wikipedia_index.ann"):
        """
        Crée un index Annoy à partir des embeddings.
        """
        Index = Create_Annoy_Index(Embeddings, num_trees=Num_Trees)
        Save_Annoy_Index(Index, File_Path)
        return Index

    def Load_Annoy_Index(self, File_Path, Embedding_Size):
        """
        Charge un index Annoy à partir d'un fichier.
        """
        Index = Load_Annoy_Index(File_Path, Embedding_Size)
        return Index
    
    def Generate_Multi_Queries(self, Query):

        Multi_Queries = Generate_Multi_Querries(Question= Query,
                                                Nb_Multi_Querries=self.Nb_Multi_Querries, 
                                                API_OLLAMA_URL=self.Api_Url,
                                                Ollama_Model_Name=self.Model_Name)
        print(f"Generated {len(Multi_Queries)} multi-queries.")
        return Multi_Queries
    

    def Retrieve_Chunks(self, Annoy_Index, Query, Chunks, Num_Results=5):

        """
        Récupère les chunks les plus pertinents en fonction de la requête.
        """
        Num_Results = self.Nb_Chunks_To_Retrieve
        if self.Use_Multi_Query : 
            Multi_Queries = self.Generate_Multi_Queries(Query=Query)

            Result_Chunks = Retrieve_Chunks_Multi_Query(self.Embedding_Model,Annoy_Index, Multi_Queries, Chunks, Num_Results,
                                                  Search_K=self.Search_K)
        elif self.Use_Rag_Fusion : 
            Multi_Queries = self.Generate_Multi_Queries(Query=Query)
            Result_Chunks = Retrieve_Chunks_RAG_Fusion(self.Embedding_Model, Annoy_Index, Multi_Queries, Chunks, Num_Results,
                                                  Search_K=self.Search_K)
        else :  
            Result_Chunks = Retrieve_Chunks_Straight(self.Embedding_Model, Annoy_Index, Query, Chunks, Num_Results,
                                                  Search_K=self.Search_K)
        return Result_Chunks
    
    def Generate_Response(self, Query, Chunk_Sources, Resource_Template=Define_Default_Resource_Template()):
        """
        Génère une réponse à partir des chunks récupérés.
        """
        print(f"Generating response for query: {Query}")
        if self.Use_Multi_Query:
            Response = Generate_Response_Multi_Querry(
                Query, Chunk_Sources, Resource_Template, self.Api_Url, self.Model_Name
            )
        elif self.Use_Rag_Fusion:
            Response = Generate_Response_Rag_Fusion(
                Query, Chunk_Sources, Resource_Template, self.Api_Url, self.Model_Name
            )
        else:
            Response = Generate_Response_Straight(
                Query, Chunk_Sources, Resource_Template, self.Api_Url, self.Model_Name
            )
        print(f"Generated response: {Response}")
        return Response



if __name__ == "__main__":

    MODEL_NAME = "llama3.1:8b"
    DATA_FOLDER = "Data_Partial/"
    EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
    API_URL = "http://localhost:11434/api/generate"
    # Load_Annoy_Index = False
    BATCH_SIZE = 16
    rag = WikipediaRAG(Data_Folder_Path=DATA_FOLDER, Embedding_Model=EMBEDDING_MODEL, Batch_Size_Embedding=BATCH_SIZE, Api_Url=API_URL, Model_Name=MODEL_NAME,
                       Use_Multi_Query=False, Use_Rag_Fusion=True,Nb_Multi_Querries=10)
    print("Chunking articles...")
    chunks = rag.Chunk_Articles(Chunk_Size=1000, Chunk_Overlap=200)
    print(f"Total chunks created: {len(chunks)}")
    print("Embedding chunks...")
    # embeddings = rag.Embed_Chunks(chunks)
    print("Creating Annoy index...")
    # annoy_index = rag.Create_Annoy_Index(embeddings, Num_Trees=100, File_Path="wikipedia_index_partial.ann")
    print("Loading Annoy index...")
    loaded_index = rag.Load_Annoy_Index("wikipedia_index_partial.ann",768 )
    query = "What is 3D Aerobatics?"
    print(f"Retrieving chunks for query: {query}")
    retrieved_chunks = rag.Retrieve_Chunks(loaded_index, query, chunks, Num_Results=5)
    print(f"Retrieved {len(retrieved_chunks)} chunks.")
    for i, chunk in enumerate(retrieved_chunks):
        print(f"Chunk {i+1}: {chunk.page_content[:100]}...")
    print("Generating response...")
    response = rag.Generate_Response(query, [chunk.page_content for chunk in retrieved_chunks])
    print(f"Response: {response}")
    # Expected output: A concise answer based on the retrieved chunks.

    
