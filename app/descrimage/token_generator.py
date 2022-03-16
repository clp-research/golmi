import secrets
import string

def generate_random_token():
    alphabet = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(alphabet) for _ in range(7))
    return token

def main():
    token = generate_random_token()
    tokens = {
        "receiver": f"{token}-1",
        "giver": f"{token}-2"
    }
    
    print("Tokens [instruction receiver == admin]:")
    for key, value in tokens.items():
        print(f"Instruction {key}:\t{value}")
    

if __name__ == "__main__":
    main()