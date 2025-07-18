import requests
from typing import List, Dict, Tuple
from tqdm import tqdm
import time
import os
import networkx as nx
import matplotlib.pyplot as plt
from adjustText import adjust_text
import wikipediaapi

WIKI_API_ENDPOINT = "https://en.wikipedia.org/w/api.php"

def Get_Category_Members(
    Category: str,
    Cmcontinue: str = None,
    Max_Members: int = None
) -> Tuple[List[Dict], str]:
    """
    Récupère les membres d'une catégorie via MediaWiki API.
    Retourne une liste de membres (pages et sous-catégories) et la valeur cmcontinue.
    """
    Params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": f"Category:{Category}",
        "cmlimit": "max",
    }
    if Cmcontinue:
        Params["cmcontinue"] = Cmcontinue

    Response = requests.get(WIKI_API_ENDPOINT, params=Params)
    Data = Response.json()
    Members = Data.get("query", {}).get("categorymembers", [])
    Cmcontinue = Data.get("continue", {}).get("cmcontinue", None)

    if Max_Members is not None:
        Members = Members[:Max_Members]

    return Members, Cmcontinue

def Get_Page_Wikitext(Title: str) -> str:
    """
    Récupère le contenu wikitexte brut d'une page via MediaWiki API.
    """
    Params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "rvprop": "content",
        "titles": Title,
        "formatversion": 2
    }
    Response = requests.get(WIKI_API_ENDPOINT, params=Params)
    Data = Response.json()
    Pages = Data.get("query", {}).get("pages", [])
    if Pages and "revisions" in Pages[0]:
        return Pages[0]["revisions"][0]["content"]
    else:
        return ""

def Fetch_Wikipedia_Category_Tree(
    Input_Category_List: List[str],
    Max_Recursion_Level: int = 3,
    Max_Pages_Per_Category: int = None,
    Max_Subcategories_Per_Category: int = None,
    Delay_Between_Requests: float = 0.5
) -> Dict[str, Tuple[List[str], Dict]]:
    """
    Construit un arbre de catégories Wikipedia sous forme {cat: ([pages], {subcats})}
    en utilisant l’API MediaWiki.

    Args:
        Input_Category_List: liste de catégories racines (sans 'Category:').
        Max_Recursion_Level: profondeur max.
        Max_Pages_Per_Category: nombre max de pages par catégorie.
        Max_Subcategories_Per_Category: nombre max de sous-catégories par catégorie.
        Delay_Between_Requests: délai entre requêtes API.

    Returns:
        Dictionnaire imbriqué {cat: ([pages], {subcats})}
    """

    def Build_Category_Tree(
        Category: str,
        Current_Level: int = 0
    ) -> Tuple[List[str], Dict]:

        Pages = []
        Subcategories = []
        Subcategories_Dict = {}

        Cmcontinue = None
        Members_Accum = []

        while True:
            Members, Cmcontinue = Get_Category_Members(
                Category,
                Cmcontinue=Cmcontinue,
                Max_Members=None  # on récupère tout, on limite après
            )
            Members_Accum.extend(Members)
            if Cmcontinue is None:
                break
            time.sleep(Delay_Between_Requests)

        if Max_Pages_Per_Category is not None:
            # filtrer uniquement pages (ns=0)
            pages_only = [m for m in Members_Accum if m['ns'] == 0]
            pages_only = pages_only[:Max_Pages_Per_Category]
        else:
            pages_only = [m for m in Members_Accum if m['ns'] == 0]

        Pages = [p['title'] for p in pages_only]

        subcats_all = [m['title'].replace("Category:", "") for m in Members_Accum if m['ns'] == 14]

        if Max_Subcategories_Per_Category is not None:
            Subcategories = subcats_all[:Max_Subcategories_Per_Category]
        else:
            Subcategories = subcats_all

        if Current_Level < Max_Recursion_Level:
            # *** Ici plus de tqdm, simple boucle ***
            for Subcat in Subcategories:
                Subcategories_Dict[Subcat] = Build_Category_Tree(Subcat, Current_Level + 1)
        else:
            Subcategories_Dict = {}

        return Pages, Subcategories_Dict

    Result_Tree = {}
    # tqdm uniquement sur la liste racine
    for Root_Cat in tqdm(Input_Category_List, desc="Root categories"):
        Result_Tree[Root_Cat] = Build_Category_Tree(Root_Cat, 0)

    return Result_Tree

def Build_Tree_Graph(Tree_Dict: Dict[str, Tuple[List[str], Dict]], Parent_Node: str = "ROOT", Graph: nx.DiGraph = None) -> nx.DiGraph:
    """
    Construit récursivement un graphe NetworkX à partir d'un arbre de catégories.

    Args:
        Tree_Dict: dict {cat: ([pages], {subcats})}
        Parent_Node: nom du noeud parent (par défaut "ROOT")
        Graph: graphe NetworkX (None => créé au début)

    Returns:
        Graphe orienté NetworkX
    """
    if Graph is None:
        Graph = nx.DiGraph()

    for Category_Name, (Page_List, Subcategory_Dict) in Tree_Dict.items():
        Graph.add_edge(Parent_Node, Category_Name)
        for Page_Title in Page_List:
            Page_Node = f"[Page] {Page_Title}"
            Graph.add_edge(Category_Name, Page_Node)
        if Subcategory_Dict:
            Build_Tree_Graph(Subcategory_Dict, Parent_Node=Category_Name, Graph=Graph)

    return Graph

def Draw_Tree_Graph_Colored(Graph: nx.DiGraph, Figure_Size=(20, 12)):

    try:
        from networkx.drawing.nx_agraph import graphviz_layout
        USE_PYGRAPHVIZ = True
    except ImportError:
        print("pygraphviz non installé, utilisation du spring_layout classique.")
        USE_PYGRAPHVIZ = False

    if USE_PYGRAPHVIZ:
        pos = graphviz_layout(Graph, prog='dot')
    else:
        pos = nx.spring_layout(Graph, k=1.2, iterations=200)

    plt.figure(figsize=Figure_Size)

    categories = [n for n in Graph.nodes() if not n.startswith("[Page]")]
    pages = [n for n in Graph.nodes() if n.startswith("[Page]")]

    nx.draw_networkx_nodes(Graph, pos, nodelist=categories, node_color='lightblue', node_size=1200, label='Categories')
    nx.draw_networkx_nodes(Graph, pos, nodelist=pages, node_color='lightgreen', node_size=700, label='Pages')
    nx.draw_networkx_edges(Graph, pos, arrows=False, alpha=0.5)

    texts = []
    for node, (x, y) in pos.items():
        texts.append(plt.text(x, y + 0.03, node, fontsize=8))

    adjust_text(
        texts,
        only_move={'points': 'y', 'texts': 'y'},
        arrowprops=dict(arrowstyle='-', color='gray', lw=0.5)
    )

    plt.title("Wikipedia Category Tree (colored)", fontsize=16)
    plt.legend(scatterpoints=1)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def Save_Wikipedia_Tree_To_Files(
    Tree_Dict: dict,
    Root_Folder: str = "Data",
    Delay_Between_Requests: float = 0.5
):
    """
    Sauvegarde le contenu des pages Wikipedia dans une arborescence de dossiers,
    structure suivant Tree_Dict.

    Args:
        Tree_Dict: arbre {cat: ([pages], {subcats})}
        Root_Folder: dossier racine
        Delay_Between_Requests: délai entre requêtes API
    """

    os.makedirs(Root_Folder, exist_ok=True)

    def Save_Pages_And_Subcats(Tree: dict, Folder: str):
        for category_name, (pages, subcats) in Tree.items():
            category_folder = os.path.join(Folder, category_name)
            os.makedirs(category_folder, exist_ok=True)

            for page_title in tqdm(pages, desc=f"Saving pages in {category_name}", unit="page"):
                wikitext = Get_Page_Wikitext(page_title)
                safe_title = page_title.replace("/", "_").replace("\\", "_")
                file_path = os.path.join(category_folder, f"{safe_title}.txt")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(wikitext)
                time.sleep(Delay_Between_Requests)

            if subcats:
                Save_Pages_And_Subcats(subcats, category_folder)

    Save_Pages_And_Subcats(Tree_Dict, Root_Folder)

def Save_Wikipedia_Tree_Flat_To_Files(
    Tree_Dict: dict,
    Root_Folder: str = "Data",
    Delay_Between_Requests: float = 0.5
):
    """
    Sauvegarde tous les textes de pages Wikipedia dans un dossier plat,
    sans structure hiérarchique.

    Args:
        Tree_Dict: arbre {cat: ([pages], {subcats})}
        Root_Folder: dossier de sortie
        Delay_Between_Requests: délai entre requêtes API
    """
    os.makedirs(Root_Folder, exist_ok=True)

    def Save_Pages_Flat(Tree: dict):
        for category_name, (pages, subcats) in Tree.items():
            for page_title in tqdm(pages, desc=f"Saving pages from {category_name}", unit="page"):
                wikitext = Get_Page_Wikitext(page_title)
                safe_title = page_title.replace("/", "_").replace("\\", "_")
                file_path = os.path.join(Root_Folder, f"{safe_title}.txt")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(wikitext)
                time.sleep(Delay_Between_Requests)
            if subcats:
                Save_Pages_Flat(subcats)

    Save_Pages_Flat(Tree_Dict)

# Exemple d'utilisation :

if __name__ == "__main__":
    Input_Categories = [
        # Physique
        "Physics", "Applied physics", "Theoretical physics", "Quantum mechanics", "Classical mechanics",
        "Thermodynamics", "Electromagnetism", "Optics", "Astrophysics", "Nuclear physics",
        "Particle physics", "Statistical mechanics", "Condensed matter physics", "Mathematical physics",
        "Plasma physics", "Geophysics", "Biophysics", "Acoustics", "Fluid mechanics", "Relativity",
        "Quantum field theory", "Solid state physics", "Optical physics", "Photonics", "Atomic physics",
        "High energy physics", "Computational physics", "Experimental physics", "Gravitational physics",
        "Quantum optics", "Nanophysics", "Cosmology", "Cryophysics", "Physics of materials",
        "Non-relativistic quantum mechanics", "String theory", "Soft matter physics",

        # Chimie
        "Chemistry", "Organic chemistry", "Inorganic chemistry", "Physical chemistry", "Analytical chemistry",
        "Biochemistry", "Theoretical chemistry", "Nuclear chemistry", "Polymer chemistry", "Electrochemistry",
        "Environmental chemistry", "Materials chemistry", "Surface chemistry", "Pharmaceutical chemistry",
        "Radiochemistry", "Supramolecular chemistry", "Green chemistry", "Computational chemistry",
        "Photochemistry", "Catalysis", "Organometallic chemistry", "Chemical kinetics", "Astrochemistry",

        # Biologie
        "Biology", "Molecular biology", "Cell biology", "Genetics", "Evolutionary biology", "Ecology",
        "Microbiology", "Botany", "Zoology", "Marine biology", "Physiology", "Neuroscience",
        "Developmental biology", "Immunology", "Bioinformatics", "Synthetic biology", "Systems biology",
        "Structural biology", "Behavioral biology", "Conservation biology", "Ethology", "Microbial ecology",
        "Genomics", "Proteomics", "Metabolomics", "Epigenetics", "Neurobiology", "Biophysics",
        "Virology", "Mycology", "Paleobiology", "Chronobiology", "Cryobiology",
        "Evolutionary developmental biology",

        # Sciences de la Terre et environnement
        "Earth sciences", "Geology", "Oceanography", "Meteorology", "Environmental science",
        "Climatology", "Volcanology", "Seismology", "Soil science", "Hydrology", "Paleontology",
        "Geochemistry", "Geomorphology", "Atmospheric sciences", "Environmental engineering",
        "Glaciology", "Geodesy", "Natural hazards", "Environmental toxicology", "Planetary science",
        "Biogeochemistry", "Hydrogeology", "Tectonics", "Remote sensing",

        # Médecine et santé
        "Medicine", "Pharmacology", "Pathology", "Immunology", "Epidemiology", "Neuroscience",
        "Surgery", "Radiology", "Oncology", "Cardiology", "Neurology", "Psychiatry",
        "Dentistry", "Public health", "Genetic counseling", "Toxicology", "Biomedical engineering",
        "Nutrition science", "Clinical research", "Anesthesiology", "Pediatrics", "Geriatrics",
        "Endocrinology", "Dermatology", "Ophthalmology", "Reproductive medicine", "Medical genetics",
        "Infectious diseases", "Hematology", "Orthopedics", "Urology", "Precision medicine",

        # Mathématiques
        "Mathematics", "Algebra", "Geometry", "Topology", "Number theory", "Calculus", "Analysis",
        "Combinatorics", "Logic", "Set theory", "Probability theory", "Statistics", "Differential equations",
        "Discrete mathematics", "Linear algebra", "Mathematical analysis", "Mathematical logic",
        "Dynamical systems", "Chaos theory", "Computational mathematics", "Mathematical modeling",
        "Complex analysis", "Real analysis", "Category theory", "Numerical analysis", "Optimization",
        "Game theory", "Graph theory", "Algebraic geometry", "Fourier analysis", "Mathematical physics",
        "Cryptography", "Stochastic processes", "Differential geometry", "Functional analysis",

        # Informatique & ingénierie
        "Computer science", "Artificial intelligence", "Machine learning", "Software engineering",
        "Electrical engineering", "Mechanical engineering", "Civil engineering", "Robotics",
        "Data science", "Computer vision", "Natural language processing", "Cybersecurity",
        "Human-computer interaction", "Network science", "Quantum computing", "Embedded systems",
        "Control theory", "Signal processing", "Bioengineering", "Systems engineering",
        "Information theory", "Distributed computing", "Computational complexity", "Cloud computing",
        "Computer graphics", "Parallel computing", "Data mining", "Computer architecture",
        "Blockchain technology", "Augmented reality", "Virtual reality", "Internet of things",
        "High-performance computing",

        # Psychologie & neurosciences
        "Psychology", "Cognitive science", "Neuroscience", "Behavioral science", "Developmental psychology",
        "Social psychology", "Clinical psychology", "Neuropsychology", "Psychophysics",
        "Experimental psychology", "Health psychology", "Educational psychology",
        "Forensic psychology", "Organizational psychology", "Positive psychology", "Psychometrics",

        # Sciences interdisciplinaires et émergentes
        "Biotechnology", "Nanotechnology", "Environmental biotechnology", "Synthetic biology",
        "Astrobiology", "Cognitive neuroscience", "Computational biology", "Systems neuroscience",
        "Sustainability science", "Renewable energy", "Climate change science", "Space science",
        "Materials science", "Quantum information science", "Science and technology studies",
        "Philosophy of science", "Science communication", "History of science",
        "Geomatics", "Urban science", "Data ethics", "Ethics of artificial intelligence",
        "Energy engineering", "Food science", "Agricultural science", "Network neuroscience",
        "Synthetic chemistry", "Bioinformatics engineering", "Planetary habitability",

        # Sciences sociales appliquées à la science
        "Science policy", "Science communication", "History of science", "Sociology of science",
        "Science education", "Research methodology", "Technology management",
        "Ethics of science", "Science diplomacy", "Citizen science",

        # Sciences de gestion liées à l'innovation scientifique
        "Innovation management", "Technology transfer", "Intellectual property", "R&D management",
        "Entrepreneurship in science", "Technology assessment",

        # Domaines appliqués
        "Environmental engineering", "Biomedical engineering", "Chemical engineering",
        "Industrial engineering", "Systems biology", "Pharmaceutical sciences",
        "Forensic science", "Materials engineering", "Aerospace engineering",
        "Nuclear engineering", "Geotechnical engineering", "Bioinformatics engineering",
    ]

    Tree = Fetch_Wikipedia_Category_Tree(
        Input_Category_List=Input_Categories,
        Max_Recursion_Level=1,
        Max_Pages_Per_Category=10,
        Max_Subcategories_Per_Category=3,
        Delay_Between_Requests=0.5
    )

    print(Tree)

    # # Construction et affichage du graphe
    # Tree_Graph = Build_Tree_Graph(Tree)
    # Draw_Tree_Graph_Colored(Tree_Graph)

    # Sauvegarde dans un dossier plat
    Save_Wikipedia_Tree_Flat_To_Files(
        Tree_Dict=Tree,
        Root_Folder="Data"
    )
