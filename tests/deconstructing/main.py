import os
import sys
import math
import hashlib

def main(FILENAME, CHUNK_SIZE, CHUNK_OUTPUT, USE_HASH=True, USE_CHUNK_HASHES=False):
    # Check if the file exists
    if not os.path.exists(FILENAME):
        print(f"File {FILENAME} does not exist.")
        sys.exit(1)

    # Check if the chunk output folder exists
    if not os.path.exists(CHUNK_OUTPUT):
        os.mkdir(CHUNK_OUTPUT)

    # Initialize hash objects
    file_hash_obj = hashlib.sha256()
    chunk_hashes = []

    # Open the file
    with open(FILENAME, "rb") as f:
        data = f.read()
        file_size = os.path.getsize(FILENAME)
        file_hash_obj.update(data)

    if USE_HASH:
        # Write the hash to a .hash file
        file_hash = file_hash_obj.hexdigest()
        with open(f"{CHUNK_OUTPUT}/{FILENAME}.hash", "w") as hash_file:
            hash_file.write(file_hash)

    # Calculate the number of chunks
    num_chunks = math.ceil(file_size / (CHUNK_SIZE * 1024 * 1024))

    # Split the file into chunks
    with open(FILENAME, "rb") as f:
        for i in range(num_chunks):
            start = i * CHUNK_SIZE * 1024 * 1024
            end = min(file_size, (i + 1) * CHUNK_SIZE * 1024 * 1024)
            chunk_data = data[start:end]
            
            # Hash each chunk if enabled
            if USE_CHUNK_HASHES:
                chunk_hash_obj = hashlib.sha256()
                chunk_hash_obj.update(chunk_data)
                chunk_hashes.append(chunk_hash_obj.hexdigest())

            # Write the chunk to a file
            with open(f"{CHUNK_OUTPUT}/{FILENAME}.{i}", "wb") as chunk_file:
                chunk_file.write(chunk_data)

    # Write chunk hashes to a .hashes file
    if USE_CHUNK_HASHES:
        with open(f"{CHUNK_OUTPUT}/{FILENAME}.hashes", "w") as hashes_file:
            hashes_file.write("\n".join(chunk_hashes))

    print(f"File {FILENAME} has been split into {num_chunks} chunks.")
    if USE_HASH:
        print(f"Hash of file: {file_hash}")
    if USE_CHUNK_HASHES:
        print(f"Chunk hashes saved to {FILENAME}.hashes.")

if __name__ == "__main__":
    FILE = "cat.png"
    SIZE = 5  # In MB
    #OUTPUT_FOLDER = "chunks"
    OUTPUT_FOLDER = "../shared_chunks"
    main(FILE, SIZE, OUTPUT_FOLDER, USE_HASH=True, USE_CHUNK_HASHES=True)
