import datetime, threading
import google.generativeai as genai
import markdown
import default_prompts
import telebot
import pandas as pd


TOKEN = "6810837032:AAHo0zKDlA6-K60HrMIcQmxMnkUIrxbroE0"

sys_exit = False


def pick(filename, data):
    import pickle

    with open(filename, 'wb') as f:
        pickle.dump(data, f)


def unpick(filename):
    import pickle

    with open(filename, 'rb') as f:
        return pickle.load(f)


def get_history(bot_id, user_id):
    all_bots = unpick("usages/" + str(user_id))
    for bot_info in all_bots:
        if bot_info["bot_id"] == bot_id:
            return bot_info["history"]


class ExcelReader:
    def __init__(self, file_path):
        self.file_path = file_path

    def read_to_dicts(self):
        try:
            df = pd.read_excel(self.file_path)
            return df.to_dict(orient='records')
        except Exception as e:
            return str(e)


# Функция для преобразования текста в Markdown
def to_markdown(text):
    """
    Replaces bullet points in the input text with Markdown bullet points and converts the modified text to Markdown format.
    :param text: The input text to be converted to Markdown format.
    :return: The input text converted to Markdown format.
    """
    text = text.replace('•', '  *')
    text = markdown.markdown(text)
    return text


# Функция для чтения файла
def read_txt_data(file_path):
    """
    Read the content of a file based on its file extension.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The content of the file if successful, or an error message if an exception occurs.
    """
    file_extension = file_path.split('.')[-1].lower()

    try:
        if file_extension in ['txt', 'csv', 'json']:
            # Обработка текстовых файлов
            with open(file_path, 'r') as file:
                return file.read()

        # Добавьте здесь другие условия для разных типов файлов
        else:
            return "Формат файла не поддерживается."
    except Exception as e:
        return f"Произошла ошибка при чтении файла: {e}"


# Класс GeminiAI
class GeminiAI:
    # Инициализация
    def __init__(self, history=[]):
        """
        Initializes the instance with an optional history parameter. Sets the API_KEY to a specific value and configures the genai with the API_KEY. Also initializes the model with 'models/gemini-pro'. If history is provided, it sets the history attribute with it. Finally, it starts the chat with the given history using the model.
        """
        self.API_KEY = "AIzaSyCTqIiFZCOM7vOwzy8GLWK4nQp-dS4qNOE"
        genai.configure(api_key=self.API_KEY)
        self.model = genai.GenerativeModel('models/gemini-pro')

        self.history = history
        self.chat = self.model.start_chat(history=self.history)

    # функция для обновления истории
    def update_history(self):
        """
        Update the chat history with the model's start chat history and return the updated chat.
        """
        self.chat.history = self.history

    def send_message(self, message):
        """
        Sends a message and updates the chat history. Returns the response message
        in Markdown format.

        Args:
            message: A string representing the message to be sent.

        Returns:
            A string in Markdown format representing the response message.
        """
        try:
            self.history.append({"role": "user", "parts": [message]})

            ######################## RESPONSE GENERATION ########################

            response = self.chat.send_message(message)

            ###################### RESPONSE GENERATION END ######################

            self.history.append({"role": "model", "parts": [response.text]})
            return response.text
        except:
            self.history.remove({"role": "user", "parts": [message]})
            self.send_message(message)

    @staticmethod
    def show_models():
        """
        A static method to show models. Iterates through the models from genai.list_models() and prints the name of the model if it supports 'generateContent' generation method.
        """
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)

    @staticmethod
    def command_executor(text):
        """
        This static method is responsible for executing a command from the given text.
        The 'text' parameter is the input text containing the command and content separated by '||'.
        It splits the text to retrieve the content and the command, performs some modifications on the command,
        and then executes it using the 'exec' function.
        The method then returns the formatted content using the 'format' method with the local variables.
        """
        content = text.split("||")[0]
        if len(text.split("||")) > 1:
            command = text.split("||")[1]
            command = command.replace("`", "")
            command = command.replace("\\", "\\\\")
            command = command.replace('python', '')
            try:
                exec(command)
            except:
                print("[ERROR] Command execution failed")
                print(command)
        return content.format(**locals())


class MessageConverter:
    def __init__(self, input_data=None):
        """
        Initialize the class with the given input data.

        Args:
            input_data: The input data to initialize the class.

        Returns:
            None
        """
        self.input_data = input_data

    def openai2gemini(self):
        """
    Converts input data to a specific format for OpenAI and returns a dictionary containing parts and role.

    Raises a ValueError for invalid input.
    """
        if "role" in self.input_data and "content" in self.input_data:
            return {"parts": [self.input_data["content"]], "role": "bot"}
        else:
            raise ValueError("Invalid input for OpenAI format")

    def gemini2openai(self):
        """
        Transforms input data into a dictionary with 'role' and 'content' keys if 'parts' and 'role' are in input data,
        and 'parts' has at least one element. Otherwise, raises a ValueError with the message "Invalid input for Bard format".
        """

        # Check if 'parts' and 'role' are in input data and 'parts' has at least one element
        if "parts" in self.input_data and "role" in self.input_data and len(self.input_data["parts"]) > 0:

            # Create dictionary with 'role' and 'content' keys
            data = {"role": self.input_data["role"], "content": self.input_data["parts"][0]}

            # Update 'role' to "assistant" if it is "model"
            if data["role"] == "model":
                data['role'] = "assistant"
            return data  # Return the dictionary
        else:
            raise ValueError("Invalid input for Bard format")  # Raise ValueError if input is invalid


class SimpleGoogleMaps:
    @staticmethod
    def generate_maps_link(address):
        """
        Generate a Google Maps link based on the provided address.

        Args:
            address (str): The address to be used in the Google Maps link.

        Returns:
            str: The generated Google Maps link.
        """

        # Заменяем пробелы на '+', чтобы создать URL-совместимый запрос
        query = address.replace(' ', '+')
        return f"https://www.google.com/maps/search/?api=1&query={query}"


def threaded(func):
    def wrapper():
        threading.Thread(target=func, daemon=True).start()

    return wrapper

