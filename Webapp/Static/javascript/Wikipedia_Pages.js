document.addEventListener('DOMContentLoaded', () => {
    const fileListEl = document.getElementById('file-list');
    const fileMessageEl = document.getElementById('file-message');
    const fileTextEl = document.getElementById('file-text');
    const searchInput = document.getElementById('search-input');
    const downloadBtn = document.getElementById('download-button');
    const fileNameEl = document.getElementById('selected-filename');

    let allFiles = [];

    // === 1. Charger la liste des fichiers depuis le serveur ===
    function loadFileList() {
        fetch('/Wikipedia_Pages/list_files')
            .then(response => response.json())
            .then(files => {
                allFiles = files;
                displayFiles(files);
            })
            .catch(() => {
                fileListEl.innerHTML = "<li style='padding:1rem;'>Erreur de chargement.</li>";
            });
    }

    // === 2. Afficher la liste des fichiers dynamiquement ===
    function displayFiles(files) {
        fileListEl.innerHTML = '';

        if (files.length === 0) {
            fileListEl.innerHTML = "<li style='padding:1rem;'>Aucun fichier trouvé.</li>";
            return;
        }

        files.forEach(filename => {
            const li = document.createElement('li');
            li.textContent = filename;
            li.classList.add('file-item');

            li.addEventListener('click', () => {
                removeActiveSelection();
                li.classList.add('active'); // Highlight selection
                displayFileContent(filename);
            });

            fileListEl.appendChild(li);
        });
    }

    // === 3. Afficher le contenu d’un fichier sélectionné ===
    function displayFileContent(filename) {
        fetch(`/Wikipedia_Pages/get_file/${encodeURIComponent(filename)}`)
            .then(response => {
                if (!response.ok) throw new Error();
                return response.text();
            })
            .then(content => {
                // Afficher le nom du fichier dans la zone de contenu (au-dessus du texte)
                fileNameEl.textContent = filename;
                fileNameEl.style.display = 'block';

                // Afficher le contenu
                fileTextEl.textContent = content;

                // Afficher et configurer le bouton de téléchargement
                downloadBtn.href = `/Wikipedia_Pages/get_file/${encodeURIComponent(filename)}`;
                downloadBtn.download = filename;
                downloadBtn.style.display = 'inline-block';
            })
            .catch(() => {
                fileNameEl.textContent = "";
                fileTextEl.textContent = "Erreur lors du chargement du fichier.";
                downloadBtn.style.display = 'none';
            });
    }

    // === 4. Supprimer la classe active sur tous les fichiers ===
    function removeActiveSelection() {
        const items = document.querySelectorAll('.file-item');
        items.forEach(item => item.classList.remove('active'));
    }

    // === 5. Filtrer les fichiers avec la recherche ===
    searchInput.addEventListener('input', () => {
        const query = searchInput.value.toLowerCase();
        const filtered = allFiles.filter(name => name.toLowerCase().includes(query));
        displayFiles(filtered);
    });

    // === 6. Initialisation ===
    loadFileList();
});
