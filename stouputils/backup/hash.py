
# Imports
import hashlib
import zipfile

from ..config import StouputilsConfig as Cfg
from ..print.message import warning


# Function to compute the SHA-256 hash of a file
def get_file_hash(file_path: str) -> str | None:
	""" Computes the SHA-256 hash of a file.

	Args:
		file_path (str): Path to the file
	Returns:
		str | None: SHA-256 hash as a hexadecimal string or None if an error occurs
	"""
	try:
		sha256_hash = hashlib.sha256()
		with open(file_path, "rb") as f:
			# Use larger chunks for better I/O performance
			while True:
				chunk = f.read(Cfg.CHUNK_SIZE)
				if not chunk:
					break
				sha256_hash.update(chunk)
		return sha256_hash.hexdigest()
	except Exception as e:
		warning(f"Error computing hash for file {file_path}: {e}")
		return None

# Function to extract the stored hash from a ZipInfo object's comment
def extract_hash_from_zipinfo(zip_info: zipfile.ZipInfo) -> str | None:
	""" Extracts the stored hash from a ZipInfo object's comment.

	Args:
		zip_info (zipfile.ZipInfo): The ZipInfo object representing a file in the ZIP
	Returns:
		str | None: The stored hash if available, otherwise None
	"""
	comment: bytes | None = zip_info.comment
	comment_str: str | None = comment.decode() if comment else None
	return comment_str if comment_str and len(comment_str) == 64 else None  # Ensure it's a valid SHA-256 hash

