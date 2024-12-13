import faiss
from sentence_transformers import SentenceTransformer
import joblib


class FaissKDB(object):
    def __init__(
        self,
        model_name="all-MiniLM-L6-v2",
        cache_folder=None,
        device="cpu",
    ):
        """
        Initializes the Faiss Knowledge Database (KDB) with a SentenceTransformer model.

        :param model_name: Name of the SentenceTransformer model to use
        :param cache_folder: Folder to cache the model files
        :param device: Device to run the model on (CPU or GPU)
        """

        # Config
        self.model_name = model_name
        self.cache_folder = cache_folder
        self.device = device
        self.texts = []

        # Create the embedding model
        self.embedding_model = SentenceTransformer(
            model_name, cache_folder=cache_folder, device=device
        )

        # Initialize FAISS indices
        self.index_l2 = None
        self.index_ip = None

    def add_embeddings(self, embeddings):
        """
        Add embeddings to the FAISS indices.

        :param embeddings: List of embeddings to add to the indices
        """
        d = embeddings.shape[1]  # Dimension of the embeddings
        if self.index_l2 is None:
            self.index_l2 = faiss.IndexFlatL2(
                d
            )  # Using L2 (Euclidean distance) as the metric

        if self.index_ip is None:
            self.index_ip = faiss.IndexFlatIP(
                d
            )  # Using inner product (cosine similarity) as the metric

        # Add the embeddings to both indices
        self.index_l2.add(embeddings)
        self.index_ip.add(embeddings)

    def add_text(self, texts: list):
        """
        Add text to the FAISS indices.

        :param texts: List of texts to add to the indices
        """
        if isinstance(texts, str):
            texts = [texts]  # Ensure input is a list of texts

        self.texts = texts
        embeddings = self.embedding_model.encode(texts)  # Generate embeddings
        faiss.normalize_L2(embeddings)  # Normalize embeddings to unit length
        self.add_embeddings(
            embeddings
        )  # Add the normalized embeddings to FAISS indices

    def export_kdb(self, filename):
        """
        Export the Knowledge Database (KDB) to a file.

        :param filename: Name of the file to save the KDB to
        """
        # Save the entire object, including texts and FAISS indices
        joblib.dump(self, f"{filename}", compress=9)

    @staticmethod
    def import_kdb(filename):
        """
        Import the Knowledge Database (KDB) from a file.
        """
        # Load the KDB from the given file
        return joblib.load(filename)

    def search(self, query, num_results=5, index_type="l2") -> list:
        """
        Search for the most similar texts in the vector space.

        :param query: The query text to search for
        :param num_results: The number of results to return
        :param index_type: The type of index to use for the search (L2, IP, or both)

        :return: List of most similar texts based on the query
        """
        query_embedding = self.embedding_model.encode(
            [query]
        )  # Generate embedding for the query
        faiss.normalize_L2(
            query_embedding
        )  # Normalize the query embedding to unit length

        results = []

        # Perform search based on selected index type (L2, IP, or both)
        if index_type.lower() == "l2" or index_type.lower() == "both":
            distances, indices = self.index_l2.search(query_embedding, num_results)
            for i in range(num_results):
                if indices[0][i] < len(self.texts):
                    results.append(
                        self.texts[indices[0][i]]
                    )  # Add the most similar texts based on L2 distance

        if index_type.lower() == "ip" or index_type.lower() == "both":
            distances, indices = self.index_ip.search(query_embedding, num_results)
            for i in range(num_results):
                if indices[0][i] < len(self.texts):
                    results.append(
                        self.texts[indices[0][i]]
                    )  # Add the most similar texts based on inner product

        return results
