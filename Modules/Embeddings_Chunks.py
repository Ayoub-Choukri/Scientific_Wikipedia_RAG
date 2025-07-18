
import annoy
from langchain.embeddings import HuggingFaceEmbeddings
from tqdm import tqdm




def Create_Embedder(Embedding_Model="all-MiniLM-L6-v2"):
    """
    Crée un objet d'embedding à partir du modèle spécifié.
    """

    return HuggingFaceEmbeddings(model_name=Embedding_Model)


def Embed_Chunks(chunks, embedder, batch_size=16):
    """
    Prend une liste de chunks et un objet d'embedding, et retourne les embeddings des chunks.
    Utilise un traitement par batch et affiche une barre de progression avec tqdm.
    """
    if not chunks:
        return []

    texts = [chunk.page_content for chunk in chunks]
    embeddings = []

    for i in tqdm(range(0, len(texts), batch_size), desc="Embedding chunks"):
        batch_texts = texts[i:i+batch_size]
        batch_embeddings = embedder.embed_documents(batch_texts)
        embeddings.extend(batch_embeddings)

    return embeddings



def Save_Embeddings(embeddings, saving_path):
    """
    Sauvegarde les embeddings dans un fichier .pt avec torch.
    """
    import torch
    torch.save(embeddings, saving_path)

def Load_Embeddings(saving_path):
    """
    Charge les embeddings depuis un fichier .pt avec torch.
    """
    import torch
    return torch.load(saving_path)



def Create_Annoy_Index(embeddings, num_trees=10):
    """
    Crée un index Annoy à partir des embeddings fournis.
    """
    if not embeddings:
        raise ValueError("Les embeddings ne peuvent pas être vides.")

    # Créer l'index Annoy
    index = annoy.AnnoyIndex(len(embeddings[0]), 'angular')

    # Ajouter les embeddings à l'index
    for i, embedding in enumerate(embeddings):
        index.add_item(i, embedding)

    # Construire l'index avec le nombre de trees spécifié
    index.build(num_trees)

    return index

def Save_Annoy_Index(index, file_path):
    """
    Sauvegarde l'index Annoy dans un fichier.
    """
    index.save(file_path)

def Load_Annoy_Index(file_path, embedding_size):
    """
    Charge un index Annoy à partir d'un fichier.
    """
    index = annoy.AnnoyIndex(embedding_size, 'angular')
    index.load(file_path)
    return index

def Search_Annoy_Index(index, query_embedding, num_results=10):
    """
    Recherche dans l'index Annoy et retourne les indices des résultats les plus proches.
    """
    if not query_embedding:
        raise ValueError("L'embedding de la requête ne peut pas être vide.")

    # Trouver les indices des résultats les plus proches
    indices = index.get_nns_by_vector(query_embedding, num_results)

    return indices

def Get_Chunk_By_Index(chunks, index):
    """
    Retourne les chunks correspondants aux indices fournis.
    """
    if not chunks or not index:
        return []

    # Extraire les chunks correspondants aux indices
    result_chunks = [chunks[i] for i in index if i < len(chunks)]

    return result_chunks


if __name__ == "__main__":
    # Example usage
    embedder = Create_Embedder(Embedding_Model="BAAI/bge-small-en")
    class Chunk:
        def __init__(self, page_content):
            self.page_content = page_content

    chunks = [
        Chunk("Water boils at 100 degrees Celsius."),
        Chunk("The capital of France is Paris."),
        Chunk("Python is a versatile programming language."),
        Chunk("Artificial Intelligence is transforming industries."),
        Chunk("The Great Wall of China is visible from space.")
    ]
    embeddings = Embed_Chunks(chunks, embedder, batch_size=2)

    print("========================== Printing Embeddings ======================")
    print(embeddings)
    index = Create_Annoy_Index(embeddings)
    Save_Annoy_Index(index, "annoy_index.ann")
    
    loaded_index = Load_Annoy_Index("annoy_index.ann", len(embeddings[0]))
    
    query_embedding = embedder.embed_query("What is the capital of France?")
    results_indices = Search_Annoy_Index(loaded_index, query_embedding, num_results=1)
    
    result_chunks = Get_Chunk_By_Index(chunks, results_indices)
    print(f"Found {len(result_chunks)} relevant chunks.")
    for chunk in result_chunks:
        print(chunk.page_content)






