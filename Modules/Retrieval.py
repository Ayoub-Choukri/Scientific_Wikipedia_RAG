
import annoy
from langchain.embeddings import HuggingFaceEmbeddings
from tqdm import tqdm
from collections import defaultdict




def Load_Annoy_Index(File_Path, Embedding_Size):
    """
    Charge un index Annoy à partir d'un fichier.
    """
    index = annoy.AnnoyIndex(Embedding_Size, 'angular')
    index.load(File_Path)
    return index

def Search_Annoy_Index(index, query_embedding, num_results=10,search_k = 500):
    """
    Recherche dans l'index Annoy et retourne les indices des résultats les plus proches.
    """
    if not query_embedding:
        raise ValueError("L'embedding de la requête ne peut pas être vide.")

    # Trouver les indices des résultats les plus proches
    indices, distances = index.get_nns_by_vector(query_embedding, num_results, search_k=search_k, include_distances=True)

    return indices, distances

def Get_Chunk_By_Index(chunks, index):
    """
    Retourne les chunks correspondants aux indices fournis.
    """
    if not chunks or not index:
        return []

    # Extraire les chunks correspondants aux indices
    result_chunks = [chunks[i] for i in index if i < len(chunks)]

    return result_chunks



def Retrieve_Chunks_Straight(Model_Name,Annoy_Index, Query, Chunks, Num_Results=10,Search_K = 500):
    """
    Récupère les chunks les plus pertinents en fonction de la requête.
    """
    if not Annoy_Index or not Query or not Chunks:
        return []

    # Créer l'embedding pour la requête
    embeddings = HuggingFaceEmbeddings(model_name=Model_Name)
    query_embedding = embeddings.embed_query(Query)
    print(f"Size of query embedding: {len(query_embedding)}")
    # Rechercher dans l'index Annoy
    indices,distances = Search_Annoy_Index(Annoy_Index, query_embedding, Num_Results,search_k=Search_K)

    # Obtenir les chunks correspondants aux indices
    result_chunks = Get_Chunk_By_Index(Chunks, indices)

    return result_chunks



# Multi_Query Retrieval

def Retrieve_Chunks_Multi_Query(Model_Name, Annoy_Index, Queries, Chunks, Num_Results=10, Search_K=500):
    """
    Récupère les chunks les plus pertinents en fonction de plusieurs requêtes, en garantissant l'unicité des résultats.
    """
    if not Annoy_Index or not Queries or not Chunks:
        return []

    unique_indices = set()
    embeddings = HuggingFaceEmbeddings(model_name=Model_Name)
    for Query in Queries:
        query_embedding = embeddings.embed_query(Query)
        print(f"Size of query embedding: {len(query_embedding)}")
        indices,distances = Search_Annoy_Index(Annoy_Index, query_embedding, Num_Results, search_k=Search_K)
        unique_indices.update(indices)

    result_chunks = Get_Chunk_By_Index(Chunks, list(unique_indices))
    return result_chunks


# RAG Fusion 
def reciprocal_rank_fusion(results_lists, k=60):
    """
    Applique la fusion Reciprocal Rank Fusion (RRF) sur plusieurs listes de résultats.
    Args:
        results_lists (List[List[Any]]): Listes de résultats (indices ou objets) à fusionner.
        k (int): Paramètre de RRF (plus grand = moins de pénalité pour les rangs élevés).
    Returns:
        List[Any]: Liste fusionnée et ordonnée selon le score RRF.
    """

    scores = defaultdict(float)
    for results in results_lists:
        for rank, item in enumerate(results):
            scores[item] += 1.0 / (k + rank + 1)
    # Trier les items selon leur score RRF décroissant
    ranked_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [item for item, score in ranked_items]


def Retrieve_Chunks_RAG_Fusion(Model_Name, Annoy_Index, Queries, Chunks, Num_Results=10, Search_K=500):
    """
    Récupère les chunks les plus pertinents en fonction de plusieurs requêtes et fusionne les résultats avec RRF.
    """
    if not Annoy_Index or not Queries or not Chunks:
        return []

    embeddings = HuggingFaceEmbeddings(model_name=Model_Name)
    all_indices = []

    for Query in tqdm(Queries, desc="Processing Queries"):
        query_embedding = embeddings.embed_query(Query)
        print(f"Size of query embedding: {len(query_embedding)}")
        indices, _ = Search_Annoy_Index(Annoy_Index, query_embedding, Num_Results, search_k=Search_K)
        all_indices.append(indices)

    fused_indices = reciprocal_rank_fusion(all_indices)
    result_chunks = Get_Chunk_By_Index(Chunks, fused_indices)
    return result_chunks



