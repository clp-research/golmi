/**
 * File: util.js
 * Contains helper functions for arrays and sets.
 */

$(document).ready(function () {
	/**
	 * Func: _vectorDist
	 * Compute the Euclidian distance between two vectors.
	 *
	 * Params:
	 * vector1 - first vector, needs to have same dimensions as vector2
	 * vector2 - second vector, needs to have same dimensions as vector1
	 *
	 * Returns:
	 * Euclidian distance
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
	/**
	 * Func: randomFromArray
	 * Choose a random element from an array.
	 *
	 * Params:
	 * array - array to select an element from
	 *
	 * Returns:
	 * randomly selected element
	 */
	document.randomFromArray = function(array) {
		return array[Math.floor(Math.random() * array.length)];
	}

	// --- set helper functions --- //
	/**
	 * Func: setEquals
	 * Check if two sets have the exact same contents.
	 * (Equality of entries is checked using the *Set.has()* function)
	 *
	 * Params:
	 * set1 - first set to check
	 * set2 - second set to check
	 *
	 * Returns:
	 * _bool_, true if sets have the same size and contain the same elements.
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
	 * Func: isSuperset
	 * Check if all elements given in the second set also occur in the first set.
	 * (Equality of entries is checked using the *Set.has()* function)
	 *
	 * Params:
	 * superSet - set that is to contain all elements of subSet
	 * subSet - set whose entries are to be contained by superSet
	 *
	 * Returns:
	 * _bool_, true if there is a superset relation
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
