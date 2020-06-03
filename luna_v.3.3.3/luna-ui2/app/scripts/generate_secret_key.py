from cryptography import fernet


def generate_application_secret_key():
    return fernet.Fernet.generate_key()


if __name__ == '__main__':
    secret_key = generate_application_secret_key()
    print(secret_key.decode())
