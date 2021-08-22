$(document).ready(function () {
	/**
	 * Compute the Euclidian distance between two vectors.
	 * @param {first vector, needs to have same dimensions as vector2} vector1
	 * @param {second vector, needs to have same dimensions as vector1} vector2
	 */
	document._vectorDist = function(vector1, vector2) {
		if (vector1.length != vector2.length) {
			console.log(`Error at _vectorDist(): Vectors need to have the same dimension. v1: ${vector1}, v2: ${vector2}`);
			return -1;
		}
		// Euclidian distance is the square root of the square differences between the vector entries
		let sumOfSquareDiffs = 0;
		for (let i=0; i<vector1.length; i++) {
			sumOfSquareDiffs += Math.pow(vector1[i] - vector2[i], 2);
		}
		return Math.sqrt(sumOfSquareDiffs);
	}
	
	// --- array helper functions --- //
	document._randomFromArray = function(array) {
		return array[Math.floor(Math.random() * array.length)];
	}

	// --- set helper functions --- //
	/**
	 * Check if two sets have the exact same contents.
	 * (Equality of entries is checked using the Set.has() function)
	 * @param {first set to check} set1
	 * @param {second set to check} set2
	 * @return bool, true if sets have the same size and contain the same elements.
	 */
	document.setEquals = function(set1, set2) {
		// check size
		if (set1.size != set2.size) return false;
		// check entries
		for (let entry of set1) {
			if (!set2.has(entry)) return false;	
		}
		return true;
	}

	/**
	 * Check if all elements given in the second set also occur in the first set.
	 * (Equality of entries is checked using the Set.has() function)
	 * @param {set that is to contain all elements of subSet} superSet
	 * @param {set whose entries are to be contained by superSet} subSet
	 * @return bool, true if there is a superset relation
	 */
	document.isSuperset = function(superSet, subSet) {
		// check size
		if (superSet.size < subSet.size) return false;
		// check entries
		for (let entry of subSet) {
			if (!superSet.has(entry)) return false;
		}
		return true;
	}
});