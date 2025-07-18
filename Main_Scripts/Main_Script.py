import sys 

MODULES_PATH = "Modules/"

sys.path.append(MODULES_PATH)



from Wikipedia_Rag import WikipediaRAG







#
CHUNKING = True
EMBEDDING_CHUNKS = True
SAVE_EMBEDDINGS = EMBEDDING_CHUNKS and True
LOAD_EMBEDDINGS = not EMBEDDING_CHUNKS and True
CREATE_ANNOY_INDEX = True
SAVE_ANNOY_INDEX = CREATE_ANNOY_INDEX and True
LOAD_ANNOY_INDEX = not CREATE_ANNOY_INDEX and True



# HYPERPARAMETERS
# ================ CHUNKING =====================
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
# ================ EMBEDDING =======================
BATCH_SIZE_EMBEDDING = 64
# You can try "BAAI/bge-base-en-v1.5" which is larger and more performant, still free for research/commercial use.
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
# EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
# La taille de l'embedding pour "BAAI/bge-base-en-v1.5" est 768 et de 
# "BAAI/bge-small-en-v1.5" est 384.
PATH_SAVING_EMBEDDINGS = "Embeddings"
# ================ ANNOY INDEX ====================
NUM_TREES = 100
PATH_SAVING_ANNOY_INDEX = "Annoy_Index"


DATA_FOLDER_PATH = "Data"
PATH_SAVING_CHUNKS = "Chunks"

RAG = WikipediaRAG(
    Data_Folder_Path=DATA_FOLDER_PATH,
    Embedding_Model=EMBEDDING_MODEL,
    Batch_Size_Embedding=BATCH_SIZE_EMBEDDING,
    Api_Url="http://localhost:11434/api/generate", 
    Model_Name="llama3"
)


if CHUNKING:
    print("============================================\n       CHUNKING ARTICLES.       \n============================================\n")
    chunks = RAG.Chunk_Articles(Chunk_Size=CHUNK_SIZE, Chunk_Overlap=CHUNK_OVERLAP)

    print(f"Number of chunks created: {len(chunks)}\n")
    # Save chunks to pickle file
    RAG.Save_Chunks(Chunks=chunks, Saving_Path=f"{PATH_SAVING_CHUNKS}/chunks.pickle")
                                                            

if EMBEDDING_CHUNKS:
    print("============================================\n       EMBEDDING CHUNKS.       \n============================================\n")
    embeddings = RAG.Embed_Chunks(Chunks=chunks)
    print(f"Number of embeddings created: {len(embeddings)}\n")
    print(f"Size of each embedding: {len(embeddings[0])}\n")
    if SAVE_EMBEDDINGS:
        print("============================================\n       SAVING EMBEDDINGS.       \n============================================\n")
        RAG.Save_Embeddings_Of_Chunks(Embeddings=embeddings, Saving_Path=f"{PATH_SAVING_EMBEDDINGS}/embeddings.pth")
        print(f"Embeddings saved to {PATH_SAVING_EMBEDDINGS}/embeddings.pth\n")

if LOAD_EMBEDDINGS:
    print("============================================\n       LOADING EMBEDDINGS.       \n============================================\n")
    embeddings = RAG.Load_Embeddings_Of_Chunks(Loading_Path=f"{PATH_SAVING_EMBEDDINGS}/embeddings.pth")
    print(f"Embeddings loaded from {PATH_SAVING_EMBEDDINGS}/embeddings.pth\n")
    print("Number of embeddings loaded: ", len(embeddings))
    print("Embedding size: ", len(embeddings[0]))

if CREATE_ANNOY_INDEX:
    print("============================================\n       CREATING ANNOY INDEX.       \n============================================\n")
    annoy_index = RAG.Create_Annoy_Index(Embeddings=embeddings, Num_Trees=NUM_TREES, File_Path=f"{PATH_SAVING_ANNOY_INDEX}/wikipedia_index.ann")
    print(f"Annoy index created with {NUM_TREES} trees and saved to {PATH_SAVING_ANNOY_INDEX}/wikipedia_index.ann\n")
    if SAVE_ANNOY_INDEX:
        print("Annoy index saved successfully.\n")

if LOAD_ANNOY_INDEX:
    print("============================================\n       LOADING ANNOY INDEX.       \n============================================\n")
    annoy_index = RAG.Load_Annoy_Index(Loading_Path=f"{DATA_FOLDER_PATH}/wikipedia_index.ann")
    print(f"Annoy index loaded from {DATA_FOLDER_PATH}/wikipedia_index.ann\n")








