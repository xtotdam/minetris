import numpy as np
import sys
from random import choice

from patterns_lists import squares as patterns, offset

sys.setrecursionlimit(5000)

letters = 'abcdefghijklmnopqrstuvwxyz'

clear_color = 	'\033[0m'
bold = 			'\033[01m'
one_back = 		'\033[1D'
one_up = 		'\033[1A'

name = '\033[36;01mMinetris' + clear_color

width = 18
height = 25
num_mines = 30

empty = 	bold + ' :: ' + clear_color
no_mines = 	'  . '

flag = 		'\033[37;07m[ F]' 		+ clear_color
explosion = '\033[37;41;01m[XX]' 	+ clear_color
mine = 		'\033[37;41;07m[XX]' 	+ clear_color

p_true  = '[::]'
p_false = '  . '

colors = [31, 32, 33, 34, 35, 36]

def pbc(i, N):
	'''Periodic boundary condition'''
	return (i % N + N) % N


def color(n):
	'''Returns color in cycle based on `colors`'''
	if not n:
		return ''
	template = '\033[{0};01m'
	c = colors[ pbc(n, len(colors)) ]
	return template.format(c)


class Minesweepa():
	'''Minesweeper'''

	game_won = False
	game_started = False
	exploded = False

	i, j = 1000, 1000
	mines_flagged = 0
	cells_opened = 0
	last_cells_opened = 0

	def __init__(self, height=7, width=7, num_mines=5):
		self.height = height if height < 25 else 25		# size of field
		self.width  = width  if width  < 25 else 25
		self.num_mines = num_mines						# number of mines

		self.field = [1] * self.num_mines + [0] * (self.height * self.width - self.num_mines)	# game field
		self.field = np.array(self.field, dtype=np.int8)

		self.field2 = np.zeros((self.height + 2 * offset, self.width + 2 * offset), dtype=np.int8)	# is used to calculate clues on it

		self.clues = 	np.zeros((self.height, self.width), dtype=np.int8)	# array with clues
		self.flagged = 	np.zeros((self.height, self.width), dtype=np.int8)	# array with flags
		self.opened = 	np.zeros((self.height, self.width), dtype=bool)		# array which contains opened cells

		self.rf = [[empty for i in xrange(self.width)] for j in xrange(self.height)]	# 'rendered field', contains all cells in printable state

		self.pattern = np.zeros((2 * offset + 1, 2 * offset + 1), dtype=np.int)		# initial pattern
		self.pr = [[empty for i in xrange(self.width)] for j in xrange(self.height)]	# `pattern rendered`, contains pattern in printable state
		self.choose_pattern()


	def __str__(self):
		return 'Use .output() instead of __str___()'


	def generate_field(self):
		'''Shuffles initial state of field,
		makes sure there is no mine on stroke coords.
		Runs only once
		'''
		if not self.game_started:
			while True:
				np.random.shuffle(self.field)
				self.field = self.field.reshape((self.height, self.width))
				if not self.field[self.i][self.j]:
					break
				self.field = self.field.flatten()
			self.game_started = True


	def generate_clues(self):
		'''Fills `clues` array with numbers of mines nearby'''
		self.field2[offset : self.height + offset, offset : self.width + offset] = self.field

		for i in range(self.height):
			for j in range(self.width):
				if self.field[i][j]:
					self.clues[i][j] = 99
				else:
					self.clues[i][j] = np.sum(self.field2[i : i + 2 * offset + 1, j : j + 2 * offset + 1] * self.pattern)


	def get_input(self, i, j, f):
		self.i = pbc(i, self.height)
		self.j = pbc(j, self.width)
		self.f = f


	def touch_field(self):
		'''Checks/sets flags, starts marking opened process, ends game'''
		if self.i < 0 or self.i >= height or self.j < 0 or self.j >= width:
			return

		if not self.opened[self.i][self.j]:
			if self.f:
				if self.flagged[self.i][self.j]:
					self.flagged[self.i][self.j] = False
					self.mines_flagged -= 1
				else:
					self.flagged[self.i][self.j] = True
					self.mines_flagged += 1
			else:
				if not self.flagged[self.i][self.j]:
					if self.field[self.i][self.j]:
						self.exploded = True
						self.gameover()
					else:
						self.mark_opened(self.i, self.j)

		if self.mines_flagged == self.num_mines:
			self.check_all_flags()
			if self.game_won:
				self.gamewon()


	def check_all_flags(self):
		'''Checks if all flags point to mines, if yes, then sets flag `gamewon`'''
		checked_mines = 0
		for i in range(self.height):
			for j in range(self.width):
				if self.flagged[i][j]:
					checked_mines += self.field[i][j]
		if checked_mines == self.num_mines:
			self.game_won = True


	def mark_opened(self, i, j):
		'''Marks field cells as once opened. Recursive!'''
		if i < 0 or i >= self.height or j < 0 or j >= self.width:
			return

		if self.opened[i][j] or self.flagged[i][j]:
			return

		self.opened[i][j] = True

		if not self.clues[i][j]:
			self.mark_opened(i + 1, j)
			self.mark_opened(i - 1, j)
			self.mark_opened(i, j + 1)
			self.mark_opened(i, j - 1)

			# diagonal revealing
			# we should be cautious with these as they can reveal mines on poor pattern choice
			self.mark_opened(i + 1, j + 1)
			self.mark_opened(i - 1, j + 1)
			self.mark_opened(i + 1, j - 1)
			self.mark_opened(i - 1, j - 1)


	def update_rendered_field(self):
		'''Updates `rf` array, that will be shown to user'''
		for i in range(self.height):
			for j in range(self.width):
				if self.flagged[i][j]:
					self.rf[i][j] = flag
				elif self.opened[i][j]:
					c = self.clues[i][j]
					if not c:
						self.rf[i][j] = no_mines
					else:
						self.rf[i][j] = color(c) + ' {:2d} '.format(c) + clear_color
				else:
					self.rf[i][j] = empty


	def show_all_clues(self):
		'''Updates `rf` to show all clues'''
		for i in xrange(self.height):
			for j in xrange(self.width):
				c = self.clues[i][j]
				if not c:
					self.rf[i][j] = no_mines
				else:
					self.rf[i][j] = color(c) + ' {:2d} '.format(c) + clear_color


	def reveal_mines(self):
		'''Puts all mines into `rf`'''
		for i in xrange(self.height):
			for j in xrange(self.width):
				if self.field[i][j]:
					if i == self.i and j == self.j:
						if self.exploded:
							self.rf[i][j] = explosion
						else:
							self.rf[i][j] = mine
					else:
						self.rf[i][j] = mine


	def gameover(self):
		'''Ends game'''
		if self.game_started:
			self.show_all_clues()
			self.reveal_mines()
			self.output()
		print 'Game over!'
		exit()


	def gamewon(self):
		'''Ends game in winning manner'''
		self.update_rendered_field()
		self.output()
		print 'You have won!'
		exit()


	def output(self):
		'''Shows game field'''
		off = 5
		self.render_pattern()
		header = self.pr[:]
		header[1] += ' ' * off + name
		header[3] += ' ' * off + 'Mines: ' + str(self.num_mines)
		header[4] += ' ' * off + 'Flags: ' + str(np.sum(self.flagged)) + ' / ' + str(self.num_mines)
		header[5] += ' ' * off + 'Cells opened: ' + str(np.sum(self.opened)) + ' / ' + str(self.width * self.height - self.num_mines)

		header = '\n'.join(header) + '\n' * 2

		output = one_back + header + bold + '[ ' + '][ '.join(letters[:self.width]) + ']' + clear_color + '\n'
		for (i,v) in enumerate(self.rf):
			for el in v:
				output += el
			output += bold + '[{:2d}]'.format(i) + clear_color + '\n'
		print '\033[' + str(self.height + 2 + 8) + 'A',		# moves cursor up
		print output[:-1]	# strip trailing '\n'


	def choose_pattern(self):
		'''Chooses current pattern for calculating clues'''
		p = choice(patterns)
		self.pattern = p

	def render_pattern(self):
		self.pr = []
		for (i, e) in enumerate(self.pattern):
			s = ''
			for (j, v) in enumerate(e):
				if i == offset and j == offset:
					s += '\033[031m'

				if v:
					s += p_true
				else:
					s += p_false

				if i == offset and j == offset:
					s += clear_color
			self.pr.append(s)


def decode_input(s):
	'''Decodes user input'''
	s = s.strip().replace(' ', '')
	parts = filter(bool, s.split(','))
	ijfs = []
	for part in parts:
		f = False
		if part.endswith('f'):
			f = True
			part = part[:-1]

		i, j = '', ''
		for c in part:
			if c in letters:
				j += c
			else:
				i += c

		j = letters.index(j)
		i = int(i)
		ijfs.append((i, j, f))
	return ijfs


if __name__ == '__main__':
	m = Minesweepa(height, width, num_mines)
	print '\n' * (height + 2 + 8),	# compensate output's compensation
	m.output()

	while True:
		try:
			ijfs = decode_input(raw_input('> \033[K'))	# '\033[K' erases line after himself
		except KeyboardInterrupt:
			print
			m.gameover()
		except ValueError:
			print one_up + one_back,
			continue
		if not len(ijfs):
			print one_up + one_back,
			continue

		for ijf in ijfs:
			m.get_input(*ijf)
			m.generate_field()
			m.generate_clues()
			m.touch_field()
		m.update_rendered_field()
		m.output()
		m.choose_pattern()
