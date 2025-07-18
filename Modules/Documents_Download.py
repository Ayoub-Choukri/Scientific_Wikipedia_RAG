import wikipediaapi
from typing import List, Dict, Tuple
from tqdm.auto import tqdm

def Fetch_Wikipedia_Category_Tree(
    Wiki_Api: wikipediaapi.Wikipedia,
    Input_Category_List: List[str],
    Max_Recursion_Level: int = 5,
    Max_Pages_Per_Category: int = None,
    Max_Subcategories_Per_Category: int = None
) -> Dict[str, Tuple[List[str], Dict]]:
    """
    Construit un arbre de catégories Wikipédia sous forme de dictionnaire récursif :
    { cat: (list_of_pages, {subcat: (...)}) }

    Args:
        Wiki_Api: Objet WikipediaAPI initialisé.
        Input_Category_List: Liste des catégories racines (sans 'Category:').
        Max_Recursion_Level: Profondeur maximale de récursion.
        Max_Pages_Per_Category: Nombre max de pages par catégorie.
        Max_Subcategories_Per_Category: Nombre max de sous-catégories par catégorie.

    Returns:
        Dictionnaire imbriqué de structure (pages, sous-catégories)
    """

    def Build_Category_Tree(
        Category_Members_Dict,
        Current_Level: int = 0
    ) -> Tuple[List[str], Dict]:
        pages = []
        subcategories = {}
        pages_added = 0
        subcats_added = 0

        for member in Category_Members_Dict.values():
            try:
                if member.ns == wikipediaapi.Namespace.MAIN:
                    if Max_Pages_Per_Category is None or pages_added < Max_Pages_Per_Category:
                        pages.append(member.title)
                        pages_added += 1
                elif member.ns == wikipediaapi.Namespace.CATEGORY:
                    if Current_Level < Max_Recursion_Level:
                        if Max_Subcategories_Per_Category is None or subcats_added < Max_Subcategories_Per_Category:
                            subcats_added += 1
                            subcat_title = member.title.replace("Category:", "")
                            # Retry logic for network errors
                            for attempt in range(3):
                                try:
                                    subcategories[subcat_title] = Build_Category_Tree(
                                        member.categorymembers,
                                        Current_Level + 1
                                    )
                                    break
                                except (requests.exceptions.RequestException, TimeoutError, requests.exceptions.ReadTimeout) as e:
                                    print(f"[Warn] Network error on '{subcat_title}' (attempt {attempt+1}/3): {e}")
                                    time.sleep(2 * (attempt + 1))
                            else:
                                print(f"[Error] Failed to fetch subcategory '{subcat_title}' after 3 attempts.")
            except (requests.exceptions.RequestException, TimeoutError, requests.exceptions.ReadTimeout) as e:
                print(f"[Error] Network error on member '{getattr(member, 'title', str(member))}': {e}")
                continue
            except Exception as e:
                print(f"[Error] Unexpected error on member '{getattr(member, 'title', str(member))}': {e}")
                continue
        return (pages, subcategories)

    result_tree = {}
    progress = tqdm(Input_Category_List, desc="Processing root categories", unit="category")

    for category_name in progress:
        formatted_category = f"Category:{category_name}" if not category_name.startswith("Category:") else category_name
        try:
            page = Wiki_Api.page(formatted_category)
            progress.set_description(f"Processing: {formatted_category}")
            if page.exists():
                for attempt in range(3):
                    try:
                        tree = Build_Category_Tree(page.categorymembers, Current_Level=0)
                        result_tree[category_name] = tree
                        break
                    except (requests.exceptions.RequestException, TimeoutError, requests.exceptions.ReadTimeout) as e:
                        print(f"[Warn] Network error on root '{formatted_category}' (attempt {attempt+1}/3): {e}")
                        time.sleep(2 * (attempt + 1))
                else:
                    print(f"[Error] Failed to fetch root category '{formatted_category}' after 3 attempts.")
            else:
                print(f"Category '{formatted_category}' does not exist.")
        except (requests.exceptions.RequestException, TimeoutError, requests.exceptions.ReadTimeout) as e:
            print(f"[Error] Network error on root '{formatted_category}': {e}")
            continue
        except Exception as e:
            print(f"[Error] Unexpected error on root '{formatted_category}': {e}")
            continue

    return result_tree


import networkx as nx
import matplotlib.pyplot as plt

def Build_Tree_Graph(Tree_Dict: Dict[str, Tuple[List[str], Dict]], Parent_Node: str = "ROOT", Graph: nx.DiGraph = None) -> nx.DiGraph:
    """
    Construit récursivement un graphe NetworkX à partir de l’arbre Wikipédia (dictionnaire imbriqué).

    Args:
        Tree_Dict: Dictionnaire récursif de type {Catégorie: ([pages], {subcats})}
        Parent_Node: Nom du nœud parent actuel (défaut = "ROOT")
        Graph: Objet Graph à construire (initialisé au début)

    Returns:
        Graphe orienté NetworkX représentant l’arborescence.
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

import networkx as nx
import matplotlib.pyplot as plt
from adjustText import adjust_text

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

    # Dessiner les nœuds catégories et pages
    nx.draw_networkx_nodes(Graph, pos, nodelist=categories, node_color='lightblue', node_size=1200, label='Categories')
    nx.draw_networkx_nodes(Graph, pos, nodelist=pages, node_color='lightgreen', node_size=700, label='Pages')
    nx.draw_networkx_edges(Graph, pos, arrows=False, alpha=0.5)

    # Créer les textes (labels) avec un petit offset vertical
    texts = []
    for node, (x, y) in pos.items():
        # On décale légèrement le texte vers le haut
        texts.append(plt.text(x, y + 0.03, node, fontsize=8))

    # Ajuster les textes pour éviter le chevauchement avec des flèches grises
    adjust_text(
        texts,
        only_move={'points':'y', 'texts':'y'},  # déplace les textes uniquement verticalement
        arrowprops=dict(arrowstyle='-', color='gray', lw=0.5)
    )

    plt.title("Wikipedia Category Tree (colored)", fontsize=16)
    plt.legend(scatterpoints=1)
    plt.axis('off')
    plt.tight_layout()
    plt.show()



import os

def Save_Wikipedia_Tree_To_Files(
    Wiki_Api: wikipediaapi.Wikipedia,
    Tree_Dict: dict,
    Root_Folder: str = "Data"
):
    """
    Sauvegarde le contenu des pages Wikipédia dans une arborescence de dossiers
    correspondant à l'arbre de catégories/pages donné.

    Args:
        Wiki_Api: instance wikipediaapi.Wikipedia initialisée.
        Tree_Dict: arbre {cat: ([pages], {subcats})}
        Root_Folder: chemin racine pour créer dossiers/fichiers.
    """

    os.makedirs(Root_Folder, exist_ok=True)

    for category_name, (pages, subcats) in tqdm(Tree_Dict.items(), desc=f"Categories in {Root_Folder}", unit="cat"):
        # Créer dossier pour la catégorie
        category_folder = os.path.join(Root_Folder, category_name)
        os.makedirs(category_folder, exist_ok=True)

        # Sauvegarder pages
        for page_title in tqdm(pages, desc=f"Pages in {category_name}", leave=False, unit="page"):
            page = Wiki_Api.page(page_title)
            if page.exists():
                # Nettoyer le titre pour un nom de fichier sûr
                safe_title = page_title.replace("/", "_").replace("\\", "_")
                file_path = os.path.join(category_folder, f"{safe_title}.txt")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(page.text)
            else:
                print(f"Page '{page_title}' introuvable.")

        # Recurse pour sous-catégories
        if subcats:
            Save_Wikipedia_Tree_To_Files(Wiki_Api, subcats, Root_Folder=category_folder)


import os
import wikipediaapi
import time
import requests
from tqdm.auto import tqdm

def Save_Wikipedia_Tree_Flat_To_Files(
    Wiki_Api: wikipediaapi.Wikipedia,
    Tree_Dict: dict,
    Root_Folder: str = "Data"
):
    """
    Sauvegarde le contenu des pages Wikipédia dans un seul dossier plat,
    sans structure hiérarchique de catégories.

    Args:
        Wiki_Api: instance wikipediaapi.Wikipedia initialisée.
        Tree_Dict: arbre {cat: ([pages], {subcats})}
        Root_Folder: chemin racine pour créer les fichiers.
    """
    os.makedirs(Root_Folder, exist_ok=True)

    def save_pages_flat(tree):
        for category_name, (pages, subcats) in tqdm(tree.items(), desc="Categories (flat)", unit="cat"):
            for page_title in tqdm(pages, desc=f"Pages in {category_name}", leave=False, unit="page"):
                try:
                    page = Wiki_Api.page(page_title)
                    if page.exists():
                        # Nettoyer le titre pour un nom de fichier sûr
                        safe_title = page_title.replace("/", "_").replace("\\", "_")
                        file_path = os.path.join(Root_Folder, f"{safe_title}.txt")
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(page.text)
                        time.sleep(0.5)  # éviter d’abuser du serveur
                    else:
                        print(f"Page '{page_title}' introuvable.")
                except (requests.exceptions.RequestException, Exception) as e:
                    print(f"[Erreur] Impossible de charger la page '{page_title}' : {e}")
                    continue
            if subcats:
                save_pages_flat(subcats)

    save_pages_flat(Tree_Dict)


if __name__ == "__main__":
    wiki = wikipediaapi.Wikipedia(
        user_agent="My_Project_Name (merlin@example.com)",
        language='en'
    )

    Input_Categories = [
        # Physique (suppléments)
        "Physics", "Applied physics", "Theoretical physics", "Quantum mechanics", "Classical mechanics",
        "Thermodynamics", "Electromagnetism", "Optics", "Astrophysics", "Nuclear physics",
        "Particle physics", "Statistical mechanics", "Condensed matter physics", "Mathematical physics",
        "Plasma physics", "Geophysics", "Biophysics", "Acoustics", "Fluid mechanics", "Relativity",
        "Quantum field theory", "Solid state physics", "Optical physics", "Photonics", "Atomic physics",
        "High energy physics", "Computational physics", "Experimental physics", "Gravitational physics",
        "Quantum optics", "Nanophysics", "Cosmology", "Cryophysics", "Physics of materials",
        "Non-relativistic quantum mechanics", "String theory", "Soft matter physics", "Classical field theory",
        "Nonlinear optics", "Condensed matter theory", "Quantum information science", "Statistical physics",
        "Thermal physics", "Accelerator physics", "Astroparticle physics", "Atomic, molecular, and optical physics (AMO)",
        "Biological physics", "Chemical physics", "Computational astrophysics", "Dark matter physics",
        "Experimental nuclear physics", "Femtochemistry", "Gravitational wave astronomy", "Hadron physics",
        "Laser physics", "Magnetohydrodynamics", "Medical physics", "Mesoscopic physics",
        "Neutrino physics", "Non-equilibrium thermodynamics", "Quantum chaos", "Quantum computing",
        "Quantum gravity", "Quantum thermodynamics", "Semiconductor physics", "Superconductivity",
        "Ultrafast physics", "X-ray physics",

        # Chimie (suppléments)
        "Chemistry", "Organic chemistry", "Inorganic chemistry", "Physical chemistry", "Analytical chemistry",
        "Biochemistry", "Theoretical chemistry", "Nuclear chemistry", "Polymer chemistry", "Electrochemistry",
        "Environmental chemistry", "Materials chemistry", "Surface chemistry", "Pharmaceutical chemistry",
        "Radiochemistry", "Supramolecular chemistry", "Green chemistry", "Computational chemistry",
        "Photochemistry", "Catalysis", "Organometallic chemistry", "Chemical kinetics", "Astrochemistry",
        "Coordination chemistry", "Medicinal chemistry", "Chemical thermodynamics", "Quantum chemistry",
        "Biophysical chemistry", "Atmospheric chemistry", "Bioinorganic chemistry", "Bioorganic chemistry",
        "Chemical biology", "Chemical engineering", "Computational drug design", "Crystal engineering",
        "Electroanalytical chemistry", "Flow chemistry", "Food chemistry", "Forensic chemistry",
        "Geochemistry", "Industrial chemistry", "Marine chemistry", "Mechanochemistry",
        "Metallurgy", "Microfluidics", "Nanoscience", "Petrochemistry",
        "Photoelectrochemistry", "Physical organic chemistry", "Polymer science", "Solid-state chemistry",
        "Sonochemistry", "Spectroscopy", "Stereochemistry", "Structural chemistry",
        "Surface science", "Synthetic chemistry", "Thermochemistry", "Water chemistry",

        # Biologie (suppléments)
        "Biology", "Molecular biology", "Cell biology", "Genetics", "Evolutionary biology", "Ecology",
        "Microbiology", "Botany", "Zoology", "Marine biology", "Physiology", "Neuroscience",
        "Developmental biology", "Immunology", "Bioinformatics", "Synthetic biology", "Systems biology",
        "Structural biology", "Behavioral biology", "Conservation biology", "Ethology", "Microbial ecology",
        "Genomics", "Proteomics", "Metabolomics", "Epigenetics", "Neurobiology", "Biophysics",
        "Virology", "Mycology", "Paleobiology", "Chronobiology", "Cryobiology",
        "Evolutionary developmental biology", "Population genetics", "Environmental biology",
        "Molecular genetics", "Cell signaling", "Synthetic ecology", "Aerobiology",
        "Agrobiology", "Anatomy", "Animal behavior", "Aquatic biology", "Astrobiology",
        "Bacteriology", "Bioclimatology", "Biodiversity", "Bioengineering", "Biogeography",
        "Biohydrology", "Biological anthropology", "Biomechanics", "Biomineralization",
        "Biostatistics", "Biotechnology", "Cancer biology", "Cell physiology",
        "Chemical biology", "Computational biology", "Conservation genetics", "Cryobiology",
        "Ecological genetics", "Endocrinology", "Entomology", "Environmental microbiology",
        "Enzymology", "Epidemiology", "Evolutionary ecology", "Evolutionary genetics",
        "Exobiology", "Extremophile biology", "Freshwater biology", "Genetic engineering",
        "Genome biology", "Histology", "Human biology", "Immunogenetics",
        "Limnology", "Marine biotechnology", "Mathematical biology", "Medical biology",
        "Microbial genetics", "Microbial physiology", "Molecular ecology", "Molecular evolution",
        "Neuroethology", "Neurogenetics", "Paleogenetics", "Parasitology",
        "Pathobiology", "Pharmacogenomics", "Phylogenetics", "Plant physiology",
        "Population biology", "Protein engineering", "Proteogenomics", "Psychobiology",
        "Radiobiology", "Reproductive biology", "Soil biology", "Systems ecology",
        "Theoretical biology", "Toxicology", "Wildlife biology", "Xenobiology",

        # Sciences de la Terre et environnement (suppléments)
        "Earth sciences", "Geology", "Oceanography", "Meteorology", "Environmental science",
        "Climatology", "Volcanology", "Seismology", "Soil science", "Hydrology", "Paleontology",
        "Geochemistry", "Geomorphology", "Atmospheric sciences", "Environmental engineering",
        "Glaciology", "Geodesy", "Natural hazards", "Environmental toxicology", "Planetary science",
        "Biogeochemistry", "Hydrogeology", "Tectonics", "Remote sensing", "Mineralogy",
        "Geophysics", "Environmental geology", "Environmental monitoring", "Atmospheric chemistry",
        "Planetary geology", "Aeronomy", "Agricultural geology", "Astrogeology",
        "Biogeography", "Coastal geography", "Cryology", "Economic geology",
        "Engineering geology", "Environmental geochemistry", "Fluvial geomorphology",
        "Geobiology", "Geochronology", "Geodynamics", "Geomicrobiology",
        "Geostatistics", "Hydrochemistry", "Hydrometeorology", "Karstology",
        "Landscape ecology", "Limnology", "Marine geology", "Meteoritics",
        "Micropaleontology", "Mineral physics", "Paleoclimatology", "Paleoecology",
        "Paleogeography", "Petrology", "Planetary geophysics", "Quaternary science",
        "Sedimentology", "Seismotectonics", "Speleology", "Stratigraphy",
        "Structural geology", "Subsurface hydrology", "Volcanic gas monitoring",
        "Weather forecasting", "Wetland science",

        # Médecine et santé (suppléments)
        "Medicine", "Pharmacology", "Pathology", "Immunology", "Epidemiology", "Neuroscience",
        "Surgery", "Radiology", "Oncology", "Cardiology", "Neurology", "Psychiatry",
        "Dentistry", "Public health", "Genetic counseling", "Toxicology", "Biomedical engineering",
        "Nutrition science", "Clinical research", "Anesthesiology", "Pediatrics", "Geriatrics",
        "Endocrinology", "Dermatology", "Ophthalmology", "Reproductive medicine", "Medical genetics",
        "Infectious diseases", "Hematology", "Orthopedics", "Urology", "Precision medicine",
        "Medical imaging", "Neonatology", "Clinical pharmacology", "Physiotherapy",
        "Medical microbiology", "Allergy and immunology", "Andrology", "Bariatrics",
        "Cardiothoracic surgery", "Clinical biochemistry", "Clinical immunology",
        "Clinical pathology", "Colorectal surgery", "Critical care medicine",
        "Cytopathology", "Emergency medicine", "Family medicine", "Forensic medicine",
        "Gastroenterology", "General practice", "Gerontology", "Gynecology",
        "Hepatology", "Histopathology", "Integrative medicine", "Internal medicine",
        "Interventional radiology", "Laboratory medicine", "Military medicine",
        "Molecular medicine", "Nephrology", "Neuropathology", "Neurosurgery",
        "Nuclear medicine", "Obstetrics", "Occupational medicine", "Oncologic pathology",
        "Osteopathy", "Otolaryngology", "Pain management", "Palliative care",
        "Parasitology", "Pediatric surgery", "Plastic surgery", "Preventive medicine",
        "Psychosomatic medicine", "Pulmonology", "Radiation oncology", "Rehabilitation medicine",
        "Rheumatology", "Sports medicine", "Telemedicine", "Transfusion medicine",
        "Transplant surgery", "Traumatology", "Tropical medicine", "Vascular surgery",
        "Veterinary medicine", "Wilderness medicine",

        # Mathématiques (suppléments)
        "Mathematics", "Algebra", "Geometry", "Topology", "Number theory", "Calculus", "Analysis",
        "Combinatorics", "Logic", "Set theory", "Probability theory", "Statistics", "Differential equations",
        "Discrete mathematics", "Linear algebra", "Mathematical analysis", "Mathematical logic",
        "Dynamical systems", "Chaos theory", "Computational mathematics", "Mathematical modeling",
        "Complex analysis", "Real analysis", "Category theory", "Numerical analysis", "Optimization",
        "Game theory", "Graph theory", "Algebraic geometry", "Fourier analysis", "Mathematical physics",
        "Cryptography", "Stochastic processes", "Differential geometry", "Functional analysis",
        "Theorems in mathematics", "Theorems in geometry", "Plane geometry", "Euclidean geometry",
        "Euclidean plane geometry", "Mathematical proofs", "Mathematical theorems", "Greek mathematics",
        "Algebraic topology", "Homological algebra", "Lie groups", "Measure theory",
        "Probability distributions", "Ergodic theory", "Non-Euclidean geometry", "Riemannian geometry",
        "Mathematical optimization", "Partial differential equations", "Model theory",
        "Commutative algebra", "Number fields", "Representation theory", "Functional equations",
        "Convex geometry", "Symplectic geometry", "Additive combinatorics", "Approximation theory",
        "Arithmetic geometry", "Axiomatic set theory", "Calculus of variations", "Descriptive set theory",
        "Enumerative combinatorics", "Finite geometry", "Geometric topology", "Harmonic analysis",
        "Homotopy theory", "K-theory", "Large deviations theory", "Low-dimensional topology",
        "Matrix theory", "Modular arithmetic", "Multilinear algebra", "Noncommutative geometry",
        "Operator theory", "Order theory", "Percolation theory", "Projective geometry",
        "Quantum algebra", "Random matrix theory", "Spectral theory", "Topological combinatorics",
        "Universal algebra", "Variational calculus", "Wavelet theory",

        # Informatique & ingénierie (suppléments)
        "Computer science", "Artificial intelligence", "Machine learning", "Software engineering",
        "Electrical engineering", "Mechanical engineering", "Civil engineering", "Robotics",
        "Data science", "Computer vision", "Natural language processing", "Cybersecurity",
        "Human-computer interaction", "Network science", "Quantum computing", "Embedded systems",
        "Control theory", "Signal processing", "Bioengineering", "Systems engineering",
        "Information theory", "Distributed computing", "Computational complexity", "Cloud computing",
        "Computer graphics", "Parallel computing", "Data mining", "Computer architecture",
        "Blockchain technology", "Augmented reality", "Virtual reality", "Internet of things",
        "High-performance computing", "Computer networks", "Formal methods", "Compiler theory",
        "Database systems", "Operating systems", "Software testing", "Cryptanalysis",
        "Computational geometry", "Machine vision", "Speech recognition", "Natural computation",
        "Embedded software", "Digital signal processing", "Control systems engineering", "Algorithm design",
        "Automata theory", "Big data", "Bioinformatics", "Computational neuroscience",
        "Computer algebra", "Computer security", "Data compression", "Data structures",
        "Decision theory", "Digital forensics", "Edge computing", "Expert systems",
        "Fuzzy logic", "Genetic algorithms", "Image processing", "Information retrieval",
        "Knowledge representation", "Logic programming", "Multi-agent systems", "Neural networks",
        "Pattern recognition", "Programming languages", "Recommender systems", "Semantic Web",
        "Social computing", "Software architecture", "Ubiquitous computing", "Web engineering",

        # Psychologie & neurosciences (suppléments)
        "Psychology", "Cognitive science", "Neuroscience", "Behavioral science", "Developmental psychology",
        "Social psychology", "Clinical psychology", "Neuropsychology", "Psychophysics",
        "Experimental psychology", "Health psychology", "Educational psychology",
        "Forensic psychology", "Organizational psychology", "Positive psychology", "Psychometrics",
        "Cognitive neuroscience", "Affective neuroscience", "Neuroimaging", "Behavioral neuroscience",
        "Psycholinguistics", "Animal cognition", "Applied psychology", "Biopsychology",
        "Child psychology", "Community psychology", "Comparative psychology", "Consumer psychology",
        "Counseling psychology", "Cultural psychology", "Differential psychology", "Ecological psychology",
        "Environmental psychology", "Evolutionary psychology", "Experimental aesthetics",
        "Family psychology", "Geriatric psychology", "Industrial psychology", "Mathematical psychology",
        "Media psychology", "Military psychology", "Moral psychology", "Music psychology",
        "Neuropsychoanalysis", "Occupational psychology", "Pediatric psychology", "Personality psychology",
        "Political psychology", "Psychoanalysis", "Psychobiology", "Psychodynamics",
        "Psychopathology", "Psychopharmacology", "Psychophysiology", "Quantitative psychology",
        "Rehabilitation psychology", "School psychology", "Sport psychology", "Traffic psychology",
        "Transpersonal psychology", "Visual perception",

        # Sciences interdisciplinaires et émergentes (suppléments)
        "Biotechnology", "Nanotechnology", "Environmental biotechnology", "Synthetic biology",
        "Astrobiology", "Cognitive neuroscience", "Computational biology", "Systems neuroscience",
        "Sustainability science", "Renewable energy", "Climate change science", "Space science",
        "Materials science", "Quantum information science", "Science and technology studies",
        "Philosophy of science", "Science communication", "History of science",
        "Geomatics", "Urban science", "Data ethics", "Ethics of artificial intelligence",
        "Energy engineering", "Food science", "Agricultural science", "Network neuroscience",
        "Synthetic chemistry", "Bioinformatics engineering", "Planetary habitability",
        "Complex systems", "Information science", "Technology ethics", "Artificial life",
        "Bioengineering", "Biomechatronics", "Computational sociology", "Cryonics",
        "Digital humanities", "Ecological engineering", "Evolutionary computation",
        "Future studies", "Genomics", "Human augmentation", "Industrial ecology",
        "Knowledge engineering", "Molecular engineering", "Neurotechnology", "Optogenetics",
        "Pervasive computing", "Quantum biology", "Robotics", "Science of team science",
        "Sociobiology", "Systems theory", "Technological singularity", "Tissue engineering",
        "Wearable technology", "Web science",

        # Sciences sociales appliquées à la science (suppléments)
        "Science policy", "Science communication", "History of science", "Sociology of science",
        "Science education", "Research methodology", "Technology management",
        "Ethics of science", "Science diplomacy", "Citizen science",
        "Philosophy of technology", "Science and society", "Academic publishing",
        "Bibliometrics", "Critical theory of technology", "Epistemology",
        "Innovation studies", "Intellectual history", "Knowledge management",
        "Metascience", "Open science", "Philosophy of mathematics",
        "Philosophy of physics", "Public understanding of science",
        "Research ethics", "Scientometrics", "Social construction of technology",
        "Sociology of knowledge", "Technology and society", "Women in science",

        # Sciences de gestion liées à l'innovation scientifique (suppléments)
        "Innovation management", "Technology transfer", "Intellectual property", "R&D management",
        "Entrepreneurship in science", "Technology assessment", "Science management",
        "Research policy", "Academic entrepreneurship", "Business analytics",
        "Corporate foresight", "Design thinking", "Digital transformation",
        "Foresight (futures studies)", "High-tech entrepreneurship",
        "Industrial innovation", "Knowledge economy", "Lean startup",
        "Open innovation", "Product lifecycle management", "Project management",
        "Research commercialization", "Risk management", "Strategic management",
        "Technology forecasting", "Technology roadmapping", "Venture capital",

        # Domaines appliqués (suppléments)
        "Environmental engineering", "Biomedical engineering", "Chemical engineering",
        "Industrial engineering", "Systems biology", "Pharmaceutical sciences",
        "Forensic science", "Materials engineering", "Aerospace engineering",
        "Nuclear engineering", "Geotechnical engineering", "Bioinformatics engineering",
        "Renewable energy engineering", "Food engineering", "Transportation engineering",
        "Acoustical engineering", "Agricultural engineering", "Automotive engineering",
        "Biological engineering", "Ceramic engineering", "Construction engineering",
        "Corrosion engineering", "Earthquake engineering", "Ecological engineering",
        "Electrical engineering", "Electronic engineering", "Energy engineering",
        "Engineering geology", "Engineering physics", "Fire protection engineering",
        "Genetic engineering", "Geological engineering", "Hydraulic engineering",
        "Manufacturing engineering", "Marine engineering", "Mechatronics",
        "Metallurgical engineering", "Mining engineering", "Nanotechnology engineering",
        "Ocean engineering", "Optical engineering", "Petroleum engineering",
        "Plastics engineering", "Power engineering", "Process engineering",
        "Quality engineering", "Radio-frequency engineering", "Robotic engineering",
        "Safety engineering", "Sanitary engineering", "Semiconductor engineering",
        "Software engineering", "Structural engineering", "Systems engineering",
        "Textile engineering", "Thermal engineering", "Tissue engineering",
        "Water resources engineering", "Wireless engineering",
    ]


    tree = Fetch_Wikipedia_Category_Tree(
        Wiki_Api=wiki,
        Input_Category_List=Input_Categories,
        Max_Recursion_Level=3,
        Max_Pages_Per_Category=100,
        Max_Subcategories_Per_Category=5
    )

    print(tree)

    # # Construire et afficher le graphe
    # Tree_Graph = Build_Tree_Graph(tree)
    # Draw_Tree_Graph_Colored(Tree_Graph)


    # # Sauvegarder les pages dans des fichiers
    Save_Wikipedia_Tree_Flat_To_Files(
        Wiki_Api=wiki,
        Tree_Dict=tree,
        Root_Folder="Data"
    )