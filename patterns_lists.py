import numpy as np
from pprint import pprint

offset = 3

simple = [
	np.zeros((7, 7), dtype=np.int8),
	np.zeros((7, 7), dtype=np.int8)
]
simple[0][2:-2,2:-2] = 1 	# 3*3 = regular minesweeper
simple[1][1:-1,1:-1] = 1 	# 5*5 = minesweeper with a feature


if __name__ == '__main__':
	for s in simple:
		print s
		print
