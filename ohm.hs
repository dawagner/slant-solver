-- SlantNode: / or \
data SlantNode = Slash | BackSlash | NoSlant
        deriving (Show, Eq)

type SlantNode' = Maybe SlantNode

type Hint = Maybe Int

-- TopHintNode down right? hint? south-east-slant?
-- HintNode down? hint? south-east-slant?
data HintTree = TopHintNode {
			down :: HintTree,
			right :: HintTree,
			hint:: Hint,
			slantNode :: SlantNode'}
              | HintNode {
			down :: HintTree,
			hint :: Hint,
			slantNode :: SlantNode'}
              | NoNode
              deriving (Show, Eq)

type TreeAddition = HintTree -> HintTree -> HintTree

data SlantCrumb = DownCrumb {
			crumbHint :: Hint,
			crumbSlantNode :: SlantNode',
			crumbRight :: HintTree}
                | RightCrumb {
			crumbHint :: Hint,
			crumbSlantNode :: SlantNode',
			crumbDown :: HintTree}
                deriving (Show, Eq)
		-- | TwoDownCrumb {
		-- 	crumbHint :: Hint,
		-- 	crumbSlantNode :: SlantNode'}

type SlantZipper = (HintTree, [SlantCrumb])

mkTopNode :: HintTree
mkTopNode = TopHintNode{
	hint = Nothing,
	slantNode = Nothing,
	down = NoNode,
	right = NoNode}

mkTopMostNode :: HintTree
mkTopMostNode = mkTopNode{slantNode = Just NoSlant}
mkTopNode' :: HintTree
mkTopNode' = mkTopMostNode

mkNode :: HintTree
mkNode = HintNode{
	hint = Nothing,
	slantNode = Nothing,
	down = NoNode}
mkNode' :: HintTree
mkNode' = mkNode{slantNode = Just NoSlant}


addRight :: TreeAddition
addRight root@TopHintNode{right = NoNode} new =
	root{right = new}

addRight TopHintNode{} _ = error "This node already has a right neighbour"

addRight HintNode{} _ = error "Can't add right to a non-top Node"

addDown :: TreeAddition
addDown root@TopHintNode{down = NoNode} new = 
	root{down = new}

addDown root@HintNode{down = NoNode} new = 
	root{down = new}

addDown _ _ = error "This node already has a down neighbour"

--
-- go RIGHT --
--
goRight :: SlantZipper -> SlantZipper
goRight (current@TopHintNode{right = right@TopHintNode{}}, crumbs) =
        (right,
	 RightCrumb (hint current) (slantNode current) (down current) : crumbs)

-- TODO
goRight (TopHintNode{right = NoNode}, _) = error "nothing on the right"

-- TODO
goRight node@(HintNode{}, _) =
	goDown . goRight . goUp $ node


--
-- go DOWN --
--
goDown :: SlantZipper -> SlantZipper
goDown (current@TopHintNode{}, crumbs) =
	(down current,
	 DownCrumb (hint current) (slantNode current) (right current) : crumbs)

goDown (HintNode{down = NoNode}, _) = error "nothing down"

goDown (current@HintNode{}, crumbs) =
	(down current,
	 DownCrumb (hint current) (slantNode current) NoNode : crumbs)


--
-- go UP --
--
goUp :: SlantZipper -> SlantZipper
goUp (current@HintNode{}, DownCrumb hint slantNode right@TopHintNode{} : cs) =
	(TopHintNode{right = right, down = current, hint = hint, slantNode = slantNode},
	 cs)

-- Contrary to the next match, the current is a top node but is on the right
-- of the board and thus doesn't have a right-neighbour
goUp (current@HintNode{}, DownCrumb hint slantNode NoNode : rcs@RightCrumb{} : cs) =
	(TopHintNode{right = NoNode, down = current, hint = hint, slantNode = slantNode},
	 rcs : cs)

goUp (current@HintNode{}, DownCrumb hint slantNode NoNode : cs) =
	(HintNode{down = current, hint = hint, slantNode = slantNode},
	 cs)

goUp (current@TopHintNode{}, RightCrumb hint slantNode down@(HintNode{}) : cs) =
	(TopHintNode{right = current, down = down, hint = hint, slantNode = slantNode},
	 cs)

goUp (_, []) = error "Already on top"


goTop :: SlantZipper -> SlantZipper
goTop zip@(node, []) = zip
goTop zip@(node, [crumb]) = goUp zip
goTop zip@(node, crumbs) = goTop (goUp zip)


-- TODO: make 'setHint' and 'setSlant' functions to be called by the following
-- ones ?
--
-- change Hint At
--
setHintAt :: Hint -> SlantZipper -> SlantZipper
setHintAt hint (node, crumbs) = (node{hint = hint}, crumbs)

--
-- change Slant At
--
setSlantAt :: SlantNode' -> SlantZipper -> SlantZipper
setSlantAt slant (node, crumbs) = (node{slantNode = slant}, crumbs)

--
-- add a node at
--
addDownAt :: HintTree -> SlantZipper -> SlantZipper
addDownAt new (current, crumbs) = (current{down = new}, crumbs)

addRightAt :: HintTree -> SlantZipper -> SlantZipper
-- TODO: allow only for TopHintNode ?
addRightAt new (current, crumbs) = (current{right = new}, crumbs)

test_top = (mkTopNode, [])
test_board' =
	addRightAt mkNode $
	addDownAt mkNode $
	test_top
