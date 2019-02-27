from collections import defaultdict


class LocalPeerStorage:
    def __init__(self):
        self.info_hashes = defaultdict(list)

    def store_peer(self, info_hash, host, port):
        self.info_hashes[info_hash].append((host, port))

    def get_peers(self, info_hash):
        return self.info_hashes[info_hash]

    def __contains__(self, info_hash):
        return info_hash in self.info_hashes
