#! /usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import itertools


class Board():
    def __init__(self, size_x, size_y):
        self.board = [[None for i in range(size_y)] for i in range(size_x)]
        self.size_x, self.size_y = size_x, size_y

        Road.init(size_x, size_y)
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
        Corner.create(self, size_x-1, size_y-1, 2)
        Corner.create(self, size_x-2, size_y-1, 2)

    @staticmethod
    def from_sgt_string(sgt_string):
        size, corners = sgt_string.split(":")
        size_x, size_y = [int(s) + 1 for s in size.split("x")]

        board = Board(size_x, size_y)
        print("size: %d, %d" % (board.size_x, board.size_y))

        current_position = 0
        for char in corners:
            if ord("a") <= ord(char) <= ord("z"):
                current_position += ord(char) - ord("a") + 1
            else:
                x = current_position % size_x
                y = current_position / size_x
                print("char: %s; position: %d; x,y = %d, %d" %
                        (char, current_position, x, y))
                board.get(x, y).hint = int(char)
                current_position += 1

        return board

    def __iter__(self):
        for corner in itertools.chain(*self.board):
            yield corner

    def add(self, corner):
        self.board[corner.x][corner.y] = corner

    def get(self, x, y):
        return self.board[x][y]

    def __repr__(self):
        return self.render()

    def render(self):
        s = []
        for i_col, col in enumerate(self.board):
            if i_col > 0:
                s.append([" "])
            s.append([])

            self.render_column(s, i_col, col)

            rectS = [''.join(l) for l in zip(*s)]

        return "\n".join(rectS)

    def render_column(self, s, index, column):
        for i_line, corner in enumerate(column):
            strHint = (str(corner.hint)
                if corner.hint is not None
                else ".")
            s[-1].append(strHint)

            if index > 0 and i_line > 0:
                strRoute = " "
                if corner.quadrants[1].connection is None:
                    strRoute = " "
                elif corner in corner.quadrants[1].connection:
                    strRoute = "\\"
                else:
                    strRoute = "/"
                s[-2].append(strRoute)


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
        return len(list(self.get_quadrants(True, True)))

    def get_nb_undecided_roads(self):
        return len(list(self.get_quadrants(False)))

    def is_solved(self):
        return self.get_nb_undecided_roads() == 0

    def get_quadrants(self, routed=None, to_self=False):
        for q in self.quadrants:
            if q is None:
                continue

            if routed is None:
                yield q

            elif routed is True:
                if to_self and q.is_routed(self):
                    yield q
                elif not to_self and q.is_routed(None):
                    yield q

            elif routed is False:
                if to_self and not q.is_routed(self):
                    yield q
                elif not to_self and not q.is_routed(None):
                    yield q

    def is_looped(self, quadrant=None):
        """@quadrant is a hint for the direction to take first"""
        if quadrant is None:
            for q in self.get_quadrants(True, True):
                if self.is_looped(q):
                    return True
            return False

        solver = LoopSolver(self, quadrant)
        return solver.solve()

    def try_solve(self):
        """ Return the nb of yet-to-be-solved roads
        """
        global test_solve_board

        if self.get_nb_undecided_roads() == 0:
            return 0, []

        #print("Solving %s" % self)

        # This list will contain the nodes around newly solved quadrants
        # try_solve() will be called on them next
        next_candidates = set()

        # If this corner has no hint, the only chance to solve it resides in
        # finding a loop
        if self.hint is None:
            self.try_solve_loops()
            # TODO: fill nexy_candidates
            return self.get_nb_undecided_roads(), []

        max_potential = (
            self.get_nb_undecided_roads()
            + self.get_nb_connected_roads()
            )
        if max_potential == self.hint:
            for q in self.get_quadrants(False):
                q.route(self)
                next_candidates.update(q.get_all_corners())

            return 0, next_candidates

        if self.get_nb_connected_roads() == self.hint:
            for q in self.get_quadrants(False):
                q.route_other(self)
                next_candidates.update(q.get_all_corners())

            return 0, next_candidates

        if self.get_nb_undecided_roads() != 0:
            self.try_solve_loops()
            # TODO: fill nexy_candidates

            return 0, []

        return self.get_nb_undecided_roads(), next_candidates


    def try_solve_loops(self):
        for q in self.get_quadrants(False):
            # If this loops, then the correct solution is
            # the other connection
            q.route(self)
            if self.is_looped(q):
                #print("self loops.  routing other")
                q.route_other(self)
                continue

            # If this loops, then the correct solution is
            # the connection from this corner (self)
            q.route_other(self)
            if q.connection[0].is_looped(q):
                #print("other loops.  routing self")
                q.route(self)
                continue

            # If nothing loops, we have no way to tell
            q.unroute()
            #print("Can't decide the loop")


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
                c.link(
                    cls.create(
                        board,
                        coords[0], coords[1],
                        nextQuadrant),
                    nextQuadrant)

        if y > 0:
            if x < board.size_x - 1:
                _walk(1)

            if x > 0:
                _walk(2)

        if y < board.size_y - 1:
            if x > 0:
                _walk(3)
            # Never walk the 4th quadrant

        return c


class LoopSolver():
    def __init__(self, corner, quadrant):
        self.orig_corner = corner
        self.orig_quadrant = quadrant
        # Replace with a real FIFO
        self.corner_fifo = []
        self.visited = set()

    def get_neighbors(self, corner, ignore_quadrant):
        others = []
        for q in corner.get_quadrants(True):
            # Is it the quadrant we come from ?
            # Then ignore
            if q == ignore_quadrant:
                continue
            # Does this quadrant connects the corner we
            # are on to anything ?
            # Then, it's a valid neighbor
            if corner in q.connection:
                others.append((q.get_neighbor(corner), q))

        return others

    def solve(self):
        first_neighbor = self.orig_quadrant.get_neighbor(self.orig_corner)
        self.corner_fifo.append((first_neighbor, None))

        while self.corner_fifo:
            corner, from_quadrant = self.corner_fifo.pop(0)
            #print("corner: %s" % corner)
            if corner in self.visited:
                return True
            self.visited.add(corner)
            neighbors = self.get_neighbors(corner, from_quadrant)
            #print("neighbors: %s" % neighbors)
            self.corner_fifo.extend(neighbors)
        else:
            #print("No loop")
            pass

        return False

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

    def get_all_corners(self):
        return itertools.chain(*self.couples)

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
    def init(cls, size_x, size_y):
        cls.__roads = [[None for i in range(size_y)]
                for i in range(size_x)]

    @classmethod
    def get(cls, x, y):
        #print("road: %s" % ((x, y),))
        if cls.__roads[x][y] is None:
            cls.__roads[x][y] = Road()
        return cls.__roads[x][y]

def build(size_x, size_y):
    return Board(size_x, size_y)

def solve(board):
    solve_passes = 0
    while True:
        passes, useless_passes = solve_pass(board)
        solve_passes += 1
        print(board)
        print(solve_passes, passes, useless_passes)
        print("")
        if passes == 0:
            break

def solve_pass(board):
    def get_unsolved(board):
        for corner in board:
            if not corner.is_solved():
                yield corner

    candidates_fifo = []
    unsolved_corners = get_unsolved(board)

    passes = useless_passes = 0

    for corner in unsolved_corners:
        candidates_fifo.append(corner)

        while candidates_fifo:
            corner = candidates_fifo.pop(0)
            passes += 1
            if corner.is_solved():
                useless_passes += 1
                continue

            left, next_candidates = corner.try_solve()
            candidates_fifo.extend(next_candidates)

            #print("%d left" % left)
            #print(board)


    return passes, useless_passes


def test():
    """test function"""
    b = build(6)

    #b.get(1,0).hint = 1
    #b.get(0,1).hint = 1
    #b.get(0,2).hint = 0
    #b.get(1,2).hint = 1

    b.get(1, 1).hint = 2
    b.get(2, 1).hint = 2
    b.get(3, 1).hint = 4
    b.get(5, 2).hint = 0
    b.get(0, 3).hint = 2
    b.get(1, 4).hint = 2
    b.get(3, 4).hint = 2
    b.get(5, 4).hint = 0
    b.get(2, 5).hint = 2
    b.get(4, 5).hint = 1


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
def test_solve():
    """test function"""
    global test_solve_board

    if test_solve_board is None:
        test_solve_board = test()
    else:
        print("continue")

    b = test_solve_board

    solve(b)

if __name__ == "__main__":
    board = build(int(sys.argv[1]))
    print(board)
