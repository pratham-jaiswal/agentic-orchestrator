## 🛠️ Sample Code Structure to Successfully Build a Tool

This folder contains sample Python scripts that demonstrate the correct structure for building tools intended for use by agents.

### ✅ Structure Guidelines:

* Define all logic inside **well-named functions**.
* The only executable block should be under `if __name__ == "__main__":`.
* **Avoid using `print()`** statements. Functions should **return values**, not display them.
* **Do not use `input()` inside any function**. If input is used, it must be within the `__main__` block only—and even that is optional.
* Imported libraries (e.g., `re`, `os`) must be **from the Python standard library** and **already installed in the environment**.

### 🔧 Example Format:

```python
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
    return process_text_input(text_input)

if __name__ == "__main__":
    text = input("Enter a word or phrase: ")
    start_check(text)
```

> 💡 **Important**: No logic, side effects, or I/O should occur outside function definitions or the `if __name__ == "__main__":` block.