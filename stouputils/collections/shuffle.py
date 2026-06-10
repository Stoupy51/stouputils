
# Imports
import hashlib
import math
import random
from collections.abc import Generator


# Functions
def affine_permutation_generator(n: int, seed: int = 0) -> Generator[int]:
	""" Generate a memory-efficient pseudo-random permutation of ``[0, n)``.

	Each ``i`` in ``[0, n)`` can only be visited once thanks to the affine bijection:
	``(a*i + b) % n`` where ``a`` and ``b`` are random integers and coprime with ``n``.

	Args:
		n    (int): Number of elements to visit.
		seed (int): Random seed for reproducibility.
	Yields:
		Generator[int]: A random permutation of ``[0, n)``.

	>>> list(affine_permutation_generator(10))
	[6, 3, 0, 7, 4, 1, 8, 5, 2, 9]
	>>> list(affine_permutation_generator(10, seed=42))
	[4, 5, 6, 7, 8, 9, 0, 1, 2, 3]

	Make sure all elements are visited:
	>>> sorted(list(affine_permutation_generator(100, seed=42))) == list(range(100))
	True

	We can have infinite permutations without blowing up memory:
	>>> for i, perm in enumerate(affine_permutation_generator(100**2000)):
	...     if i > 4: break
	...     print(f"Permutation {i}: {str(perm)[:20]}...")
	Permutation 0: 60923891346657165714...
	Permutation 1: 77383182119683752460...
	Permutation 2: 93842472892710339206...
	Permutation 3: 10301763665736925951...
	Permutation 4: 26761054438763512697...
	"""
	randomizer = random.Random(seed)

	# Choose a multiplier 'a' that is coprime with 'n'
	# This ensures the mapping is a bijection module 'n'
	while True:
		a: int = randomizer.randint(1, n - 1)
		if math.gcd(a, n) == 1:
			break

	# Random offset 'b' in [0, n)
	b: int = randomizer.randint(0, n - 1)

	# Generate a full permutation of [0, n) via an affine bijection: (a*i + b) % n
	for i in range(n):
		yield (a * i + b) % n


def feistel_permutation_generator(n: int, seed: int = 0) -> Generator[int]:
	""" Generate a memory-efficient pseudo-random permutation of ``[0, n)``.

	This uses a Feistel network to build a bijective mapping over a power-of-two
	domain, then filters values outside ``[0, n)``.

	Unlike affine permutations, this produces a much more "shuffle-like" order
	with significantly reduced algebraic structure.

	Args:
		n    (int): Number of elements to visit.
		seed (int): Random seed for reproducibility.

	Yields:
		Generator[int]: A pseudo-random permutation of ``[0, n)``.

	>>> list(feistel_permutation_generator(10))
	[1, 8, 0, 5, 3, 6, 9, 7, 4, 2]
	>>> list(feistel_permutation_generator(10, seed=42))
	[5, 3, 1, 6, 4, 2, 8, 0, 9, 7]

	Make sure all elements are visited:
	>>> sorted(list(feistel_permutation_generator(100, seed=42))) == list(range(100))
	True

	We can have infinite permutations without blowing up memory:
	>>> for i, perm in enumerate(feistel_permutation_generator(100**2000)):
	...     if i > 4: break
	...     print(f"Permutation {i}: {str(perm)[:20]}...")
	Permutation 0: 56877730339930604433...
	Permutation 1: 31140272880303506593...
	Permutation 2: 89677538354424247341...
	Permutation 3: 94477358131828883980...
	Permutation 4: 37089694092416945146...
	"""
	# Choose bit width as next power-of-two domain
	bits: int = max(2, (n - 1).bit_length())
	if bits % 2 != 0:
		bits += 1

	# Domain is a power-of-two, so we can use a Feistel network
	domain: int = 1 << bits

	# Generate full permutation of the extended domain, then filter
	for i in range(domain):
		y: int = FeistelHelpers.permute(i, seed, bits)
		if y < n:
			yield y


# Helper functions
class FeistelHelpers:
	""" Helper functions for the Feistel permutation generator. """
	@staticmethod
	def round_prf(seed: int, round_no: int, value: int, out_bits: int) -> int:
		""" Small deterministic Pseudo-Random Function (PRF) used inside the Feistel network.

		Args:
			seed     (int):    Seed for the PRF.
			round_no (int):    Round number (0-3).
			value    (int):    Input value.
			out_bits (int):    Output bit-width.
		Returns:
			int: The PRF output.
		"""
		# Convert input to bytes
		seed_bytes: bytes = seed.to_bytes(8, "little", signed=False)
		round_bytes: bytes = round_no.to_bytes(4, "little", signed=False)
		value_bytes: bytes = value.to_bytes((out_bits + 7) // 8, "little", signed=False)

		# Hash the input
		h = hashlib.shake_256()
		h.update(seed_bytes)
		h.update(round_bytes)
		h.update(value_bytes)

		# Convert hash to int
		return int.from_bytes(h.digest((out_bits + 7) // 8), "little", signed=False)

	@staticmethod
	def permute(x: int, seed: int, bits: int, rounds: int = 4) -> int:
		""" Feistel permutation over a fixed bit-width domain.

		Args:
			x      (int):    Input value.
			seed   (int):    Random seed for the permutation.
			bits   (int):    Bit-width of the domain.
			rounds (int):    Number of rounds to apply (default: 4).
		Returns:
			int: Permuted value.
		"""
		# Split bit-space into two equal halves for Feistel structure
		half: int = bits // 2
		mask: int = (1 << half) - 1

		# Partition input into left and right halves
		left: int = x >> half
		right: int = x & mask

		# Apply Feistel rounds: each round mixes right half into left via PRF
		for r in range(rounds):
			pseudo_random: int = FeistelHelpers.round_prf(seed, r, right, half) & mask

			# Standard Feistel swap + XOR diffusion step
			left, right = right, (left ^ pseudo_random) & mask

		# Recombine halves into final permuted value
		return (left << half) | right

