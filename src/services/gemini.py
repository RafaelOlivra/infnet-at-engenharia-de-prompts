import time
import google.generativeai as genai
import os
import json

from models.ai_response import AIResponse
from load_dotenv import load_dotenv

# Load the environment variables
load_dotenv()


class Gemini:
    """
    A simple class that implements methods to generate content using the Google Gemini API.
    """

    def __init__(
        self,
        api_key: str = None,
        system_prompt: str = None,
        model_name: str = "gemini-1.5-flash",
    ):
        """
        Initialize the Gemini class with the API key and system prompt.

        :param api_key: The API key for the Google Gemini API
        :param system_prompt: The system prompt to use for generating content
        """

        # Set the API key, either from the environment or directly from the parameter
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required for Google Gemini API")

        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        self.response = None
        self.system_prompt = system_prompt

    # ----------------------------
    # Main Methods
    # ----------------------------

    def ask(self, prompt: str) -> AIResponse:
        """
        Ask the Gemini API a question based on a prompt.

        :param prompt: The prompt to ask the Gemini API
        :return: The response from the Gemini API
        """
        try:
            # Clean previous response
            self.response = None

            # Count the time taken to generate the content
            start_time = time.time()

            model = genai.GenerativeModel(
                model_name=self.model_name, system_instruction=self.system_prompt
            )
            response = model.generate_content(prompt)

            # Calculate the time taken to generate the content
            end_time = time.time()
            time_taken = end_time - start_time

            print(
                "[Gemini] Content ready! Time taken: {:.2f} seconds".format(time_taken)
            )
            response = {"response": response.text, "provider": "Google Gemini"}
            self.response = response

            # Print the response
            print(response)

            return response

        except Exception as e:
            print(f"{str(e)}")
            return None

    def ask_and_execute(self, prompt: str) -> AIResponse:
        """
        Ask the Gemini API a question based on a prompt and execute the generated code.

        :param prompt: The prompt to ask the Gemini API
        :return: The response from the Gemini API
        """
        self.ask(prompt)
        self._execute()
        return self.response

    def ask_and_generate_python_code(self, prompt: str) -> str:
        """
        Ask the Gemini API a question based on a prompt and generate Python code.

        :param prompt: The prompt to ask the Gemini API
        :return: The generated Python code
        """
        self.ask(prompt)
        return self._to_python_code()

    def ask_and_generate_json_str(self, prompt: str) -> str:
        """
        Ask the Gemini API a question based on a prompt and generate a JSON string.

        :param prompt: The prompt to ask the Gemini API
        :return: The generated JSON string
        """
        self.ask(prompt)
        return self._to_json_str()

    # ----------------------------
    # Utils
    # ----------------------------

    def _to_python_code(self) -> str:
        """
        Convert the response to Python code.

        :return: The generated Python code
        """
        code = self.response["response"]
        code = code.replace("```python", "").replace("```", "")

        self.response["response"] = code
        return code

    def _to_json_str(self) -> str:
        """
        Convert the response to a JSON string.

        :return: The generated JSON string
        """

        json_string = self.response["response"]
        json_string = json_string.replace("```json", "").replace("```", "")
        # Convert the string to a json object
        json_str = None
        try:
            json_str = json.loads(json_string)
            json_str = json.dumps(json_str, indent=4)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON string: {str(e)}")
            return None

        self.response["response"] = json_str
        return json_str

    def _execute(self) -> None:
        """Execute the generated code."""
        code = self._to_python_code()
        exec(code)
