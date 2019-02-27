from hashlib import sha256
from os import urandom


class TokenManager:
    def __init__(self):
        self.tokens = {}
        self.token_key = self.generate_token_key()
        self.issued_tokens = {}

    def generate_token(self, host: bytes):
        return sha256(host + self.token_key).digest()

    @staticmethod
    def generate_token_key():
        return urandom(20)

    def issue_token(self, node_id):
        token = self.generate_token_key()
        self.issued_tokens[node_id] = token
        return token

    def verify_token(self, node_id, token):
        return self.issued_tokens[node_id] == token
