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
        # Save parameters
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

    # Add embeddings to the FAISS indices
    def add_embeddings(self, embeddings):
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

    # Process the text embeddings and add them to the indices
    def add_text(self, texts: list):
        if isinstance(texts, str):
            texts = [texts]  # Ensure input is a list of texts

        self.texts = texts
        embeddings = self.embedding_model.encode(texts)  # Generate embeddings
        faiss.normalize_L2(embeddings)  # Normalize embeddings to unit length
        self.add_embeddings(
            embeddings
        )  # Add the normalized embeddings to FAISS indices

    # Export the Knowledge Database (KDB) to a file
    def export_kdb(self, filename):
        # Save the entire object, including texts and FAISS indices
        joblib.dump(self, f"{filename}", compress=9)

    # Import the Knowledge Database (KDB) from a file
    @staticmethod
    def import_kdb(filename):
        # Load the KDB from the given file
        return joblib.load(filename)

    # Search for the most similar texts in the vector space
    def search(self, query, num_results=5, index_type="l2") -> list:
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
