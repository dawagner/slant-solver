#! /usr/bin/env python
# -*- coding: utf-8 -*-
import sys


class Board():
	def __init__(self, size):
		self.board = [[None for i in range(size)] for i in range(size)]
		self.size = size

		Road.init(size)
		# the board is layout out with (0, 0) at the top-left
		# we need to create the first node (at the bottom-right) as if
		# we come from outside the board toward the second quadrant.
		# See Corner.__init__
		# The first node can walk to half of the other nodes;
		# We need a second node to create the other half.
		# To convince yourself that there cannot be less than two
		# separate roads, start from any node and by making only
		# diagonal moves, try to cover the whole board.  You won't be
		# able to.
		Corner.create(self, size-1, size-1, 2)
		Corner.create(self, size-2, size-1, 2)

	def add(self, corner):
		self.board[corner.x][corner.y] = corner

	def get(self, x, y):
		return self.board[x][y]

	def __repr__(self):
		return self.board.__repr__()

	def render(self):
		s = []
		#s.append([""] * self.size)
		for i_col, col in enumerate(self.board):
			if i_col > 0:
				s.append([" "])
			s.append([])
			for i_line, corner in enumerate(col):
				strHint = (str(corner.hint)
					if corner.hint is not None
					else ".")
				s[-1].append(strHint)

				if i_col > 0 and i_line > 0:
					strRoute = " "
					if corner.quadrants[1].connection is None:
						strRoute = " "
					elif corner in corner.quadrants[1].connection:
						strRoute = "\\"
					else:
						strRoute = "/"
					s[-2].append(strRoute)

		print(s)
		rectS = [''.join(l) for l in zip(*s)]

		print("\n".join(rectS))


class Corner():
	""" A "Node" (that can have a value between 0 and 4 or no value) in
	    the game
	"""

	def __init__(self, x, y):
		self.x, self.y = x, y
		self.hint = None
		# quadrants are defined in the trigo order:
		# 2 | 1 
		#---x---
		# 3 | 4 
		# Example in case of the lower-right corner:
		# 2 |
		#---x
		# This table contains the reference to the other corners
		self.quadrants = [None, None, None, None]

	def __hash__(self):
		return hash((self.x, self.y))

	def __eq__(self, other):
		return self.x == other.x and self.y == other.y

	def __repr__(self):
		return "<Corner (%d, %d): %s>" % (self.x, self.y, self.hint)

	def get_neighbor_coords(self, quadrant):
		addVector = [(1, -1), (-1, -1), (-1, 1), (1, 1)]
		add = addVector[quadrant-1]
		return self.x + add[0], self.y + add[1]

	def get_road_coords(self, quadrant):
		addVector = [(0, -1), (-1, -1), (-1, 0), (0, 0)]
		add = addVector[quadrant-1]
		return self.x + add[0], self.y + add[1]

	@staticmethod
	def _opposite_quadrant(quadrant):
		return (quadrant-1 + 2) % 4 + 1

	def get_road(self, quadrant):
		return self.quadrants[quadrant - 1]

	def get_neighbor(self, quadrant):
		return self.get_road(quadrant).get_neighbor(self)

	def do_link(self, quadrant, road):
		""" Make %quadrant point to %road
		"""
		self.quadrants[quadrant - 1] = road

	def link(self, other, quadrant):
		""" Stores the information about this node's neighbor.
		
		This does not mean that they are connected, but that
		they can be.
		Does the same operation on the neighbor.
		"""
		#print("node: %s->%d" % ((self.x, self.y),quadrant))
		road = Road.get(*self.get_road_coords(quadrant))
		road.construct(self, other)

		self.do_link(quadrant, road)
		other.do_link(Corner._opposite_quadrant(quadrant), road)

	def route(self, quadrant):
		self.get_road(quadrant).route(self)

	def unroute(self, quadrant):
		self.get_road(quadrant).unroute()

	def get_nb_connected_roads(self):
		return len(list(self.get_quadrants(True)))
		#return sum(q.is_routed(self)
		#		for q in self.quadrants
		#		if q)

	def get_nb_undecided_roads(self):
		return len(list(self.get_quadrants(False)))
		#return sum(not q.is_routed(None)
		#		for q in self.quadrants
		#		if q)

	def get_quadrants(self, routed=None):
		for q in self.quadrants:
			if q is None:
				continue

			if routed is None:
				yield q
			if routed is True and q.is_routed(None):
				yield q
			elif routed is False and not q.is_routed(None):
				yield q

	def is_looped(self, quadrant=None):
		"""@quadrant is a hint for the direction to take first"""
		if quadrant is None:
			for q in self.get_quadrants(True):
				if self.is_looped(q):
					return True
			return False

		def get_neighbors(corner, ignore_quadrant):
			others = []
			for q in corner.get_quadrants(True):
				if q == ignore_quadrant:
					continue
				others.append((q.get_neighbor(corner), q))

			return others

		# Replace with a real FIFO
		corner_fifo = []
		visited = set()
		corner = quadrant.get_neighbor(self)
		corner_fifo.append((corner, quadrant))

		while corner_fifo:
			corner, from_quadrant = corner_fifo.pop(0)
			print("corner: ")
			if corner in visited:
				return True
			visited.add(corner)
			neighbors = get_neighbors(corner, from_quadrant)
			print("neighbors: %s" % neighbors)
			corner_fifo.extend(neighbors)
		else:
			print("No loop")

		return False




	def try_solve(self):
		""" Return the nb of yet-to-be-solved roads
		"""
		print("Solving %s" % self)
		if self.hint is None:
			return self.get_nb_undecided_roads()

		if self.get_nb_undecided_roads() == self.hint and self.hint == 0:
			return 0

		if self.get_nb_undecided_roads() == 0:
			return 0

		if self.get_nb_undecided_roads() == self.hint:
			print("let's route all my surrounding")
			for q in self.quadrants:
				if q is None:
					continue
				if not q.is_routed(None):
					q.route(self)

		if self.get_nb_connected_roads() == self.hint:
			print("let's anti-route all my surrounding")
			for q in self.quadrants:
				if q is None:
					continue
				if not q.is_routed(None):
					q.route_other(self)

		if self.get_nb_undecided_roads() != 0:
			print("let's try to make loops")
			self.try_solve_loops()

		return self.get_nb_undecided_roads()


	def try_solve_loops(self):
		for q in self.get_quadrants(False):
			print("trying %s" % q)
			# If this loops, then the correct solution is
			# the other connection
			q.route(self)
			if self.is_looped(q):
				print("self loops.  routing other")
				q.route_other(self)
				continue

			# If this loops, then the correct solution is
			# the connection from this corner (self)
			q.route_other(self)
			if q.connection[0].is_looped(q):
				print("other loops.  routing self")
				q.route(self)
				continue

			# If nothing loops, we have no way to tell
			q.unroute()
			print("Can't decide the loop")



	@classmethod
	def create(cls, board, x, y, fromQuadrant):
		c = cls(x, y)
		existing = board.get(c.x, c.y)
		if existing:
			return existing

		board.add(c)

		fromQuadrant = c._opposite_quadrant(fromQuadrant)

		def _walk(nextQuadrant):
			coords = c.get_neighbor_coords(nextQuadrant)
			if nextQuadrant != fromQuadrant:
				c.link(cls.create(board, coords[0], coords[1], nextQuadrant), nextQuadrant)

		if y > 0:
			if x < board.size - 1:
				#print("toward 1")
				_walk(1)

			if x > 0:
				#print("toward 2")
				_walk(2)

		if y < board.size - 1:
			if x > 0:
				#print("toward 3")
				_walk(3)
			# Never walk the 4th quadrant

		#print("Fin du chemin pour %s" % c)

		return c

class Road():
	__roads = []

	def __init__(self):
		""" Road constructor
		
		%couples is the list of couple of corners that may be
		connected through this road.
		%connection is the actual couple connected through this road
		"""
		self.couples = []
		self.connection = None

	def construct(self, *corners):
		""" Adds a couple to the list of potential connections

		TODO: change the name ...
		"""
		self.couples.append(corners)

	def route(self, corner):
		""" Connect a corner with its pair
		"""
		couple = next(c for c in self.couples if corner in c)
		self.connection = couple

	def route_other(self, corner):
		""" Connect the other pair than this corner's
		"""
		couple = next(c for c in self.couples if corner not in c)
		self.connection = couple

	def unroute(self):
		""" Remove the current connection
		"""
		self.connection = None

	def get_neighbor(self, corner):
		couple = next(c for c in self.couples if corner in c)
		other = next(c for c in couple if corner != c)
		return other

	def is_routed(self, corner=None):
		any = self.connection is not None
		if corner is None:
			return any
		return any and corner in self.connection

	def __repr__(self):
		couples = ["***%s***" % (c,)
				if c == self.connection
				else "%s" % (c,)
				for c in self.couples]

		return "<Road %s>" % "; ".join(couples)

	@classmethod
	def __iter__(cls):
		return cls.__roads.__iter__()

	@classmethod
	def init(cls, size):
		cls.__roads = [[None for i in range(size)] for i in range(size)]

	@classmethod
	def get(cls, x, y):
		#print("road: %s" % ((x, y),))
		if cls.__roads[x][y] is None:
			cls.__roads[x][y] = Road()
		return cls.__roads[x][y]

def build(size):
	return Board(size)

def test():
	b = build(3)

	#b.get(1,0).hint = 1
	#b.get(0,1).hint = 1
	#b.get(0,2).hint = 0
	#b.get(1,2).hint = 1

	b.get(1, 0).hint = 2
	b.get(0, 2).hint = 0

	#b.get(0,1).route(4)
	#b.get(1,1).route(4)
	#b.get(0,0).route(4)
	#b.get(1,0).route(4)

	print("nb of connections for (1,1):%d" %
			b.get(1, 1).get_nb_connected_roads())
	print("nb of undecided Roads around (1,1):%d" %
			b.get(1, 1).get_nb_undecided_roads())

	return b

test_solve_board = None
def solve():
	global test_solve_board

	if test_solve_board is None:
		test_solve_board = test()
	else:
		print("continue")

	b = test_solve_board

	for col in b.board:
		for corner in col:
			if corner.hint is None:
				continue
			left = corner.try_solve()
			print("%d left" % left)


if __name__ == "__main__":
	board = build(int(sys.argv[1]))
	print(board)
