import numpy as np
import sys

sys.setrecursionlimit(5000)

# TODO remove `numpy` dependency

letters = 'abcdefghijklmnopqrstuvwxyz'

width = 25
height = 25
num_mines = 30
shell_size = 2

clear_color = '\033[0m'
bold = '\033[01m'

empty = '  . '

flag = 		'\033[37;07m[ F]' 		+ clear_color
explosion = '\033[37;41;01m[XX]' 	+ clear_color
mine = 		'\033[37;41;07m[XX]' 	+ clear_color

colors = [31, 32, 33, 34, 35, 36]

def pbc(i, N):
	return (i % N + N) % N

def color(n):
	if not n:
		return ''
	template = '\033[{0};01m'
	c = colors[ pbc(n, len(colors)) ]
	return template.format(c)


class Minesweepa():
	first_touch = True
	game_over = False
	game_won = False
	game_started = False
	i, j = 1000, 1000
	mines_flagged = 0

	def __init__(self, height=5, width=5, num_mines=5, shell_size=1):
		self.height = height if height < 25 else 25
		self.width = width if width < 25 else 25
		self.num_mines = num_mines
		self.shell_size = shell_size

		self.field = [1] * self.num_mines + [0] * (self.height * self.width - self.num_mines)
		self.field = np.array(self.field, dtype=np.int8)

		self.clues = np.zeros((self.height, self.width), dtype=np.int8)

		self.flagged = [[0 for i in xrange(self.width)] for j in xrange(self.height)]
		self.opened = [[0 for i in xrange(self.width)] for j in xrange(self.height)]

		self.rf = [[empty for i in xrange(self.width)] for j in xrange(self.height)]

	def __str__(self):
		output = bold + '[ ' + '][ '.join(letters[:self.width]) + ']' + clear_color + '\n'
		for (i,v) in enumerate(self.rf):
			for el in v:
				output += el
			output += bold + '[{:2d}]'.format(i) + clear_color + '\n'
		return output[:-1]

	def generate_field(self, i, j):
		'''i, j -- coords of first stroke => no mines there'''
		self.first_touch = False
		while True:
			np.random.shuffle(self.field)
			self.field = self.field.reshape((self.height, self.width))
			if not self.field[i][j]:
				break
		self.generate_clues()

	def generate_clues(self):
		field2 = np.zeros((self.height + 2 * self.shell_size, self.width + 2 * self.shell_size), dtype=int)
		field2[self.shell_size : self.height + self.shell_size, self.shell_size : self.width + self.shell_size] = self.field

		for i in range(self.height):
			for j in range(self.width):
				if self.field[i][j]:
					self.clues[i][j] = 99
				else:
					self.clues[i][j] = np.sum(field2[i : i + 2 * self.shell_size + 1, j : j + 2 * self.shell_size + 1])
		del(field2)

	def touch_field(self, i, j, f):
		self.i = i
		self.j = j
		self.game_started = True

		if i < 0 or i >= height or j < 0 or j >= width:
			return

		if self.first_touch:
			self.generate_field(i, j)
			self.first_touch = False

		if not self.opened[i][j]:
			if f:
				if self.flagged[i][j]:
					self.flagged[i][j] = False
					self.rf[i][j] = empty
					self.mines_flagged -= 1
				else:
					self.flagged[i][j] = True
					self.rf[i][j] = flag
					self.mines_flagged += 1
			else:
				if not self.flagged[i][j]:
					if self.field[i][j]:
						self.gameover()
					else:
						self.reveal_clues(i, j)

		if self.mines_flagged == self.num_mines:
			self.check_all_flags()
			if self.game_won:
				self.gamewon()

	def check_all_flags(self):
		checked_mines = 0
		for i in range(self.height):
			for j in range(self.width):
				if self.flagged[i][j]:
					checked_mines += self.field[i][j]
		if checked_mines == self.num_mines:
			self.game_won = True


	def reveal_clues(self, i, j):
		if i < 0 or i >= self.height or j < 0 or j >= self.width:
			return

		if self.opened[i][j] or self.flagged[i][j]:
			return

		self.opened[i][j] = True
		c = self.clues[i][j]
		self.rf[i][j] = color(c) + ' {:2d} '.format(c) + clear_color

		if not self.clues[i][j]:
			self.reveal_clues(i + 1, j)
			self.reveal_clues(i - 1, j)
			self.reveal_clues(i, j + 1)
			self.reveal_clues(i, j - 1)

	def starting_screen(self):
		mid = self.height / 2
		left = self.height - mid
		s = ' ' * (self.width * 2 - 7) + 'Strange Minesweepa'
		return '\n' * mid + s + '\n' * left

	def reveal_mines(self):
		for i in xrange(self.height):
			for j in xrange(self.width):
				if self.field[i][j]:
					if i == self.i and j == self.j:
						self.rf[i][j] = explosion
					else:
						self.rf[i][j] = mine

	def gameover(self):
		print
		if self.game_started:
			self.reveal_mines()
			print '\033[' + str(self.height + 2) + 'A' + str(self)
		print 'Game over! Bye'
		exit()

	def gamewon(self):
		print
		print '\033[' + str(self.height + 3) + 'A' + str(self)
		print 'You have won!'
		exit()


	def output(self):
		output = bold + '[ ' + '][ '.join(letters[:self.width]) + ']' + clear_color + '\n'
		for (i,v) in enumerate(self.rf):
			for el in v:
				output += el
			output += bold + '[{:2d}]'.format(i) + clear_color + '\n'
		print '\033[' + str(self.height + 2) + 'A' + output[:-1]

def decode_input(s):
	s = s.strip().replace(' ', '')
	f = False
	if s.endswith('f'):
		f = True
		s = s[:-1]

	i, j = '', ''
	for c in s:
		if c in letters:
			j += c
		else:
			i += c

	j = letters.index(j)
	i = int(i)
	return i, j, f


m = Minesweepa(height, width, num_mines, shell_size)
print m.starting_screen()

while True:
	try:
		i, j, f = decode_input(raw_input('> \033[K'))
	except KeyboardInterrupt:
		m.gameover()
	except ValueError:
		continue

	m.touch_field(i, j, f)
	m.output()
