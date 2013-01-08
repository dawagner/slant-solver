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

class Corner():
	""" A "Node" (that can have a value between 0 and 4 or no value) in
	    the game
	"""

	def __init__(self, x, y): #, hintValue):
		self.x, self.y = x, y
		self.hintValue = None
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
		return "<Corner (%d, %d): %s>" % (self.x, self.y, self.hintValue)

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
		other = next(c for c in couple if corner != c)

	# TODO: route_other

	def unroute(self):
		""" Remove the current connection
		"""
		self.connection = None

	def __repr__(self):
		couples = ["***%s***" % (c,)
				if c == self.connection
				else "%s" % (c,)
				for c in self.couples]

		return "<Road %s>" % "; ".join(couples)

	@classmethod
	def init(cls, size):
		cls.__roads = [[None for i in range(size)] for i in range(size)]

	@classmethod
	def get(cls, x, y):
		#print("road: %s" % ((x, y),))
		if not cls.__roads[x][y]:
			cls.__roads[x][y] = Road()
		return cls.__roads[x][y]

def build(size):
	return Board(size)

if __name__ == "__main__":
	board = build(int(sys.argv[1]))
	print(board)
