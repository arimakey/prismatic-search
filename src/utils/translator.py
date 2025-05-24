from agents import api

def translate_to_english(text: str) -> str:
    """Translate Spanish text to English using the AI API.

    Args:
        text (str): Text in Spanish to translate

    Returns:
        str: Translated text in English
    """
    conversation = [
        {
            "role": "system",
            "content": (
                "You are a professional translator. Translate the given Spanish text to English. "
                "Provide only the translation without any additional comments or explanations."
            )
        },
        {"role": "user", "content": text}
    ]
    
    return api.get_completion(conversation)