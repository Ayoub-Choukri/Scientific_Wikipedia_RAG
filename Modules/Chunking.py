from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pathlib import Path




def Create_Text_Splitter(Chunk_Size=1000, Chunk_Overlap=200):
    # Use RecursiveCharacterTextSplitter with English-specific separators for better performance
    Text_Splitter = RecursiveCharacterTextSplitter(
        chunk_size=Chunk_Size,
        chunk_overlap=Chunk_Overlap,
        separators=    ["$$", "\\[", "\\]", "\n\n", "\n", ".", "!", "?", ",", " ", ""]
    )
    return Text_Splitter




def Chunk_Text(text, text_splitter):
    # Crée un vrai objet Document
    document = Document(page_content=text)
    chunks = text_splitter.split_documents([document])
    return chunks



from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pathlib import Path


def Chunk_Text_From_File_Path(file_path, text_splitter):
    """
    Prend un chemin vers un fichier (string ou Path), le charge et le découpe en chunks.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"❌ Le fichier '{file_path}' n'existe pas.")
    
    loader = TextLoader(str(path))
    documents = loader.load()
    chunks = text_splitter.split_documents(documents)
    return chunks




def Chunk_Text_Of_Folder(Folder_Path, Text_Splitter,Extension=".txt"):
    Folder_Path = Path(Folder_Path)
    Chunks = []
    for File in Folder_Path.glob(f"*{Extension}"):
        if not File.is_file():
            continue

        File_Chunks = Chunk_Text_From_File_Path(File, Text_Splitter)
        Chunks.extend(File_Chunks)
    return Chunks




import json
import pickle
from tqdm.auto import tqdm

def Save_Chunks_To_Pickle(Chunks, Saving_Path):
    """
    Sauvegarde les chunks dans un fichier pickle.
    """
    with open(Saving_Path, "wb") as f:
        pickle.dump(Chunks, f)
    print(f"✅ Chunks saved to {Saving_Path}")


def Load_Chunks_From_Pickle(Saving_Path):
    """
    Charge les chunks à partir d'un fichier pickle.
    """
    with open(Saving_Path, "rb") as f:
        Chunks = pickle.load(f)
    print(f"✅ Chunks loaded from {Saving_Path}")
    return Chunks


def Access_Text_Of_Chunk(chunk):
    """
    Accède au texte d'un chunk.
    """
    if hasattr(chunk, "page_content"):
        return chunk.page_content
    elif isinstance(chunk, dict) and "page_content" in chunk:
        return chunk["page_content"]
    else:
        raise ValueError("Chunk must have a 'page_content' attribute or key.")

def Acces_Text_Of_Chunks(Chunks):
    """
    Retourne une liste des textes de chaque chunk dans Chunks, avec une barre de progression.
    """
    Texts_Of_Chunks = []
    for chunk in tqdm(Chunks, desc="Extraction des textes des chunks"):
        Texts_Of_Chunks.append(Access_Text_Of_Chunk(chunk))
    return Texts_Of_Chunks


if __name__ == "__main__":
    # Example usage
    splitter = Create_Text_Splitter(Chunk_Size=1000, Chunk_Overlap=200)
    folder_path = "Data/"
    chunks = Chunk_Text_Of_Folder(folder_path, splitter)
    print(f"Total chunks created: {len(chunks)}")
    for i, chunk in enumerate(chunks[:5]):  # Print first 5 chunks
        print(f"Chunk {i+1}: {chunk.page_content[:100]}...")  # Print first 100 characters of each chunk
