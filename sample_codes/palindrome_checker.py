import re

def is_palindrome(text):
    '''Checks if cleaned text is a palindrome.'''
    cleaned = re.sub(r'[^A-Za-z0-9]', '', text.lower())
    return cleaned == cleaned[::-1]

def process_text_input(text_input):
    '''Processes user input and checks for palindrome.'''
    if not text_input.strip():
        return "❌ Input cannot be empty."
    result = is_palindrome(text_input)
    return f"✅ '{text_input}' is a palindrome." if result else f"❌ '{text_input}' is not a palindrome."

def start_check(text_input):
    '''Starts the palindrome check process.'''
    output = process_text_input(text_input)
    return output

if __name__ == "__main__":
    text = input("Enter a word or phrase: ")
    start_check(text)