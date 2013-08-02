-- SlantNode: / or \
data SlantNode = Slash | BackSlash | NoSlant
        deriving (Show)

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
              deriving (Show)

type TreeAddition = HintTree -> HintTree -> HintTree

data SlantCrumb = DownCrumb {
			crumbHint :: Hint,
			crumbSlantNode :: SlantNode',
			crumbRight :: HintTree}
                | RightCrumb {
			crumbHint :: Hint,
			crumbSlantNode :: SlantNode',
			crumbDown :: HintTree}
                deriving (Show)
		-- | TwoDownCrumb {
		-- 	crumbHint :: Hint,
		-- 	crumbSlantNode :: SlantNode'}

type SlantZipper = (HintTree, [SlantCrumb])

mkTopMostNode :: HintTree
mkTopMostNode = TopHintNode NoNode NoNode Nothing (Just NoSlant)

mkTopNode :: HintTree
mkTopNode = TopHintNode NoNode NoNode Nothing Nothing
mkTopNode' :: HintTree
mkTopNode' = TopHintNode NoNode NoNode Nothing (Just NoSlant)

mkNode :: HintTree
mkNode = HintNode NoNode Nothing Nothing
mkNode' :: HintTree
mkNode' = HintNode NoNode Nothing (Just NoSlant)


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
goRight (TopHintNode down right@TopHintNode{} hint slantNode, crumbs) =
        (right, RightCrumb hint slantNode down : crumbs)

-- TODO
goRight (TopHintNode down NoNode hint slantNode, crumbs) = error "nothing on the right"

-- TODO
goRight node@(HintNode down hint slantNode, crumbs) =
	goDown . goRight . goUp $ node


--
-- go DOWN --
--
goDown :: SlantZipper -> SlantZipper
goDown (TopHintNode down right hint slantNode, crumbs) =
	(down,
	 DownCrumb hint slantNode right : crumbs)

goDown (HintNode NoNode hint slantNode, crumbs) = error "nothing down"

goDown (HintNode down hint slantNode, crumbs) =
	(down,
	 DownCrumb hint slantNode NoNode : crumbs)


--
-- go UP --
--
goUp :: SlantZipper -> SlantZipper
goUp (current@HintNode{}, DownCrumb hint slantNode right@TopHintNode{} : cs) =
	(TopHintNode{right = right, down = current, hint = hint, slantNode = slantNode},
	 cs)

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
setHintAt :: SlantZipper -> Hint -> SlantZipper
setHintAt (node, crumbs) hint = (node{hint = hint}, crumbs)

--
-- change Slant At
--
setSlantAt :: SlantZipper -> SlantNode' -> SlantZipper
setSlantAt (node, crumbs) slant = (node{slantNode = slant}, crumbs)

--
-- add a node at
--
addDownAt :: HintTree -> SlantZipper -> SlantZipper
addDownAt new (current, crumbs) = (current{down = new}, crumbs)

addRightAt :: HintTree -> SlantZipper -> SlantZipper
-- TODO: allow only for TopHintNode ?
addRightAt new (current, crumbs) = (current{right = new}, crumbs)

test_board :: HintTree
test_board =
	TopHintNode 
		(HintNode NoNode Nothing Nothing)
		(TopHintNode
			(HintNode NoNode (Just 1) Nothing)
			NoNode
			Nothing
			Nothing)
		(Just 1)
		(Just NoSlant)

test_top = (mkTopNode, [])
test_board' =
	addRightAt mkNode $
	addDownAt mkNode $
	test_top

test_zip = (test_board, [])
