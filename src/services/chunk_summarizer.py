import time


class ChunkSummarizer:
    def __init__(
        self,
        ai_provider,
        text,
        window_size=200,
        overlap_size=50,
        chunk_prompt_template=None,
        chunk_prompt_append=None,
        final_summary_prompt_template=None,
        final_summary_prompt_append=None,
    ):
        """
        Initializes the summarizer.

        :param ai_provider: An AI provider with an 'ask' method for generating responses
        :param text: Input text to summarize (str or list of strings)
        :param window_size: Number of lines or characters per chunk
        :param overlap_size: Overlap between chunks
        :param chunk_prompt_template: Optional template for chunk summarization
        :param final_summary_prompt_template: Optional template for final summary generation
        """
        # # Ensure text is a list
        self.text = text

        # Chunk-related parameters
        self.window_size = window_size
        self.overlap_size = overlap_size

        # Default prompt templates
        self.chunk_prompt_template = chunk_prompt_template or (
            "Provide a concise and comprehensive summary of the following text, "
            "capturing the main ideas and key points:\n\n{content}"
            + (chunk_prompt_append or "")
        )

        self.final_summary_prompt_template = final_summary_prompt_template or (
            """Based on the following chunk summaries:
            - {combined_summaries}
            ######
            Create a final, cohesive summary that:
            1. Captures the most essential information
            2. Maintains the core narrative
            3. Removes redundant information

            Provide the summary as plain text string.
            Do not add any additional information or other fields."""
            + (final_summary_prompt_append or "")
        )

        # AI Provider
        self.ai_provider = ai_provider

        # Check if we have an ask method or return an error
        if not hasattr(self.ai_provider, "ask"):
            raise ValueError(
                "AI provider must have an 'ask' method that accepts a prompt."
            )

        # Process text into chunks
        self.chunks = self._text_to_chunks()
        self.chunks_summaries = []

    def _text_to_chunks(self) -> list:
        """Breaks the text into chunks based on window_size and overlap_size."""
        n = self.window_size  # Size of each chunk
        m = self.overlap_size  # Overlap between chunks

        # If text is a string, split by lines
        if isinstance(self.text, str):
            self.text = self.text.split("\n")

        # If text is a list of strings, join into a single string
        if isinstance(self.text, list):
            self.text = "\n".join(self.text)

        # If text is not a string, raise an error
        if not isinstance(self.text, str):
            raise ValueError("Input text must be a string or a list of strings.")

        # Split text into chunks
        chunks = []
        for i in range(0, len(self.text), n - m):
            chunk = self.text[i : i + n]
            chunks.append(chunk)

        return chunks

    def _create_chunk_prompt(self, chunk) -> str:
        """
        Generates a prompt for summarizing a chunk of text.

        :param chunk: The chunk of text to summarize
        :return: The prompt for summarizing the chunk
        """
        content = "\n".join(chunk)
        return self.chunk_prompt_template.format(content=content).strip()

    def _summarize_chunks(self) -> list:
        """
        Summarizes each chunk of text using the AI provider.

        :return: List of summaries for each chunk
        """
        chunk_summaries = []
        for i, chunk in enumerate(self.chunks):
            print(f"Summarizing chunk {i + 1} of {len(self.chunks)}")

            # Create prompt for this chunk
            prompt = self._create_chunk_prompt(chunk)

            # Use AI provider's ask method to get summary
            summary = self.ask(prompt)
            if summary:
                chunk_summaries.append(summary)
                time.sleep(2)

        self.chunks_summaries = chunk_summaries
        return chunk_summaries

    def summarize(self) -> str:
        """
        Generates the final summary based on chunk summaries.

        :return: Dictionary containing the final summary
        """
        print("Summarizing text...")

        # Summarize chunks if not already done
        if not self.chunks_summaries:
            self._summarize_chunks()

        # Combine chunk summaries
        combined_summaries = "\n- ".join(self.chunks_summaries)

        # Create final summary prompt
        final_prompt = self.final_summary_prompt_template.format(
            combined_summaries=combined_summaries
        ).strip()

        print("Generating final summary...")

        # Get final summary using AI provider
        final_summary = self.ask(final_prompt)

        return final_summary

    def ask(self, prompt: str) -> str:
        """
        Ask the AI provider a question based on a prompt.

        :param prompt: The prompt to ask the AI provider
        :return: The response from the AI provider
        """
        response = self.ai_provider.ask(prompt)

        # Check if we got a dict with "response" key
        if isinstance(response, dict) and "response" in response:
            response = response["response"]

        return str(response) if response else ""
