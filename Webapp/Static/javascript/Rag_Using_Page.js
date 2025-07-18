// RAG_Using_Page.js
// Front-end logic to connect the UI to your Flask RAG endpoints.

document.addEventListener("DOMContentLoaded", () => {
  const BASE_URL = "/Rag_Using_Page";

  // DOM ELEMENTS
  const btnLoadAnnoy = document.getElementById("btn-load-annoy");
  const btnSubmitRagMode = document.getElementById("btn-submit-rag-mode");
  const ragModeSelect = document.getElementById("rag-mode");
  const nbChunksToRetrieveInput = document.getElementById("nb-chunks-to-retrieve");
  const nbMultiQueriesInput = document.getElementById("nb-multi-queries");

  const questionForm = document.getElementById("question-form");
  const questionInput = document.getElementById("question-input");
  const responseOutput = document.getElementById("response-output");

  const chunksList = document.getElementById("chunks-list");
  const chunkSearch = document.getElementById("chunk-search");
  const chunkText = document.getElementById("chunk-text");
  const chunkTitleDisplay = document.getElementById("selected-chunk-title");

  let cachedChunks = [];

  btnLoadAnnoy.disabled = true;

  async function fetchJSON(url, options = {}) {
    const res = await fetch(url, options);
    if (!res.ok) {
      const msg = await res.text();
      throw new Error(`${res.status} – ${msg}`);
    }
    return res.json();
  }

  function setLoading(el, isLoading) {
    if (!el) return;
    el.disabled = isLoading;
    el.dataset.originalText = el.dataset.originalText || el.textContent;
    el.textContent = isLoading ? "Loading…" : el.dataset.originalText;
  }

  function renderChunkItems(chunks) {
    chunksList.innerHTML = "";
    if (!chunks.length) {
      chunksList.innerHTML = "<li><em>Aucun chunk trouvé.</em></li>";
      return;
    }

    chunks.forEach((chunk, idx) => {
      const li = document.createElement("li");
      li.className = "chunk-item";
      li.dataset.chunkIndex = idx;
      li.textContent = chunk.title || `Chunk ${idx + 1}`;

      li.addEventListener("click", () => {
        document.querySelectorAll(".chunk-item.active").forEach((el) =>
          el.classList.remove("active")
        );
        li.classList.add("active");

        chunkTitleDisplay.textContent = li.textContent;
        chunkTitleDisplay.style.display = "block";
        chunkText.innerHTML = "<em>Chargement du contenu…</em>";

        const index = parseInt(li.dataset.chunkIndex);
        fetch(`${BASE_URL}/Access_Text_Of_Chunk`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ chunk_index: index }),
        })
          .then((res) => res.json())
          .then((data) => {
            if (data.status === "success") {
              chunkText.textContent = data.text;
            } else {
              chunkText.innerHTML = `<span class='error'>Erreur: ${data.message}</span>`;
            }
          })
          .catch((err) => {
            console.error("Erreur de chargement du chunk:", err);
            chunkText.innerHTML = `<span class='error'>Erreur lors de la récupération du chunk.</span>`;
          });
      });

      chunksList.appendChild(li);
    });
  }

  // ===== CONFIGURATION RAG =====
  btnSubmitRagMode.addEventListener("click", async () => {
    setLoading(btnSubmitRagMode, true);

    const ragMode = ragModeSelect.value;
    const nbChunksToRetrieve = parseInt(nbChunksToRetrieveInput.value) || 10;
    const nbMultiQueries = parseInt(nbMultiQueriesInput.value) || 3;

    const ragConfig = {
      use_multi_query: ragMode === "multi-query",
      use_rag_fusion: ragMode === "rag-fusion",
      nb_chunks_to_retrieve: nbChunksToRetrieve,
      nb_multi_queries: nbMultiQueries,
    };

    try {
      const res = await fetchJSON(`${BASE_URL}/set_rag_mode`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(ragConfig),
      });

      console.info(res.message);
      alert("Mode RAG configuré avec succès !");
      btnLoadAnnoy.disabled = false;
    } catch (err) {
      console.error("Erreur configuration RAG:", err);
      alert(`Erreur: ${err.message}`);
    } finally {
      setLoading(btnSubmitRagMode, false);
    }
  });

  // ===== CHARGER INDEX + CHUNKS =====
  btnLoadAnnoy.addEventListener("click", async () => {
    setLoading(btnLoadAnnoy, true);
    try {
      const res = await fetchJSON(`${BASE_URL}/Load_Annoy_Index`);
      console.info(res.message);
      await loadChunks();
      alert("Index et chunks chargés ! Posez votre question.");
    } catch (err) {
      console.error(err);
      alert(`Erreur: ${err.message}`);
    } finally {
      setLoading(btnLoadAnnoy, false);
    }
  });

  async function loadChunks() {
    const res = await fetchJSON(`${BASE_URL}/Load_Chunks`);
    console.info(res.message);
    cachedChunks = [];
    renderChunkItems([]);
    chunkText.innerHTML = "<em>Sélectionnez un chunk pour afficher son contenu.</em>";
  }

  // ===== POSER UNE QUESTION =====
  questionForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = questionInput.value.trim();
    if (!query) return;

    responseOutput.innerHTML = "<em>Veuillez patienter…</em>";

    try {
      const result = await fetchJSON(`${BASE_URL}/Retrieve_And_Generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      responseOutput.textContent = result.response;
      cachedChunks = result.relevant_chunks || [];
      renderChunkItems(cachedChunks);
    } catch (err) {
      console.error(err);
      responseOutput.innerHTML = `<span class="error">${err.message}</span>`;
    }
  });

  // ===== RECHERCHE DANS LES CHUNKS =====
  chunkSearch.addEventListener("input", () => {
    const term = chunkSearch.value.toLowerCase();
    Array.from(chunksList.children).forEach((li) => {
      const match = li.textContent.toLowerCase().includes(term);
      li.style.display = match ? "block" : "none";
    });
  });
});