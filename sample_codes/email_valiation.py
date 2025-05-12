import re

def sanitize_email(email):
    return email.strip()

def is_valid_email(email):
    pattern = r'^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$'
    return re.match(pattern, email) is not None

def process_email(user_input):
    email = sanitize_email(user_input)
    if is_valid_email(email):
        return f"✅ Valid email: {email}"
    else:
        return "❌ Invalid email format."

if __name__ == "__main__":
    user_input = input("Enter an email address: ")
    process_email(user_input)
