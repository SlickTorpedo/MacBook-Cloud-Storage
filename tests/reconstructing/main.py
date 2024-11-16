import os
import sys
import hashlib

def main(CHUNK_FOLDER, OUTPUT_FILE, CHECK_HASH=True, CHECK_CHUNK_HASHES=False):
    # Check if the chunk folder exists
    if not os.path.exists(CHUNK_FOLDER):
        print(f"Folder {CHUNK_FOLDER} does not exist.")
        sys.exit(1)

    # Read the file-wide hash
    hash_value = None
    if CHECK_HASH:
        hash_file = f"{CHUNK_FOLDER}/{OUTPUT_FILE}.hash"
        if os.path.exists(hash_file):
            with open(hash_file, "r") as f:
                hash_value = f.read()
            print(f"Stored file hash: {hash_value}")
        else:
            print(f"Hash file {hash_file} does not exist. Skipping hash check.")

    # Read the chunk hashes
    chunk_hashes = []
    if CHECK_CHUNK_HASHES:
        hashes_file = f"{CHUNK_FOLDER}/{OUTPUT_FILE}.hashes"
        if os.path.exists(hashes_file):
            with open(hashes_file, "r") as f:
                chunk_hashes = f.read().splitlines()
            print(f"Loaded chunk hashes from {hashes_file}.")
        else:
            print(f"Hashes file {hashes_file} does not exist. Skipping chunk hash check.")

    # Get the list of chunks
    chunks = [chunk for chunk in os.listdir(CHUNK_FOLDER) if not chunk.endswith(".hash") and not chunk.endswith(".hashes")]
    chunks.sort()

    # Reconstruct the file
    with open(OUTPUT_FILE, "wb") as f:
        for i, chunk in enumerate(chunks):
            with open(f"{CHUNK_FOLDER}/{chunk}", "rb") as chunk_file:
                chunk_data = chunk_file.read()

                # Verify chunk hash if enabled
                if CHECK_CHUNK_HASHES:
                    chunk_hash_obj = hashlib.sha256()
                    chunk_hash_obj.update(chunk_data)
                    chunk_hash = chunk_hash_obj.hexdigest()
                    if chunk_hashes and chunk_hash != chunk_hashes[i]:
                        print(f"Chunk {i} hash mismatch! Expected {chunk_hashes[i]}, got {chunk_hash}.")
                        sys.exit(1)

                f.write(chunk_data)

    print(f"Chunks in {CHUNK_FOLDER} have been reconstructed into {OUTPUT_FILE}.")

    # Verify file-wide hash
    if CHECK_HASH and hash_value:
        with open(OUTPUT_FILE, "rb") as f:
            data = f.read()
            file_hash_obj = hashlib.sha256()
            file_hash_obj.update(data)
            file_hash = file_hash_obj.hexdigest()
            print(f"Output file hash: {file_hash}")
            if file_hash == hash_value:
                print("File hashes match.")
            else:
                print("File hashes do not match!")

if __name__ == "__main__":
    #CHUNK_FOLDER = "chunks"
    CHUNK_FOLDER = "../shared_chunks"
    OUTPUT_FILE = "cat.png"
    main(CHUNK_FOLDER, OUTPUT_FILE, CHECK_HASH=True, CHECK_CHUNK_HASHES=True)
