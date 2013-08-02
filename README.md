slant-solver
============

Python solver for the "Slant" game from sgt-puzzles collection

For now, it can only solve Easy-graded puzzles.

How To Use
----------

* Open slant, go to the "Game" menu and click on "Specific"
* Copy the string.
* Run a python interpreter from the slant-solver directory
* In the python interpreter:
  * `board = slant.Board.from_sgt_string("<paste the string here>")`
  * `slant.solve(board)`
