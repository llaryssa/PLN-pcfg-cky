import nltk
from nltk.grammar import Nonterminal
from nltk.corpus import treebank
from nltk import treetransforms
from nltk import induce_pcfg
from nltk import nonterminals
from nltk.tree import Tree
from nltk import PCFG

import numpy as np
from sets import Set
from random import shuffle

np.set_printoptions(suppress=True)

########### FUNCTIONS ###########3

foundRoot = False
parsingTree = []
indexMaxScore = -1
terminalsParents = []

def buildTree(score, back, nwords, nont, currentBack, indexI, indexJ):
    global parsingTree
    global foundRoot
    global indexMaxScore
    global terminalsParents

    if not foundRoot:
        maxScore = -1;
        for i in range(0, len(nont)):
            if score[i][0][nwords] > maxScore:
                maxScore = score[i][0][nwords]
                indexMaxScore = i
        foundRoot = True
        top = nont[indexMaxScore]
        currentBack = back[indexMaxScore][0][nwords]
        parsingTree.append([top,0,nwords])

        buildTree(score, back, nwords, nont, currentBack, 0, nwords)
    else:
        if len(currentBack) == 3:
            split = currentBack[0]
            firstNT = currentBack[1]
            firstNTIndex = nont.index(firstNT)
            secondNT = currentBack[2]
            secondNTIndex = nont.index(secondNT)

            parsingTree.append([firstNT, indexI, split])
            currentBack = back[firstNTIndex][indexI][split];
            buildTree(score, back, nwords, nont, currentBack, indexI, split)

            parsingTree.append([secondNT,split,indexJ])
            currentBack = back[secondNTIndex][split][indexJ];
            buildTree(score, back, nwords, nont, currentBack, split, indexJ)
        elif len(currentBack) == 1:
            nt = currentBack[0]
            if nt in nont:
                ntIndex = nont.index(nt)

                parsingTree.append([nt, indexI, indexJ])
                currentBack = back[ntIndex][indexI][indexJ];
                buildTree(score, back, nwords, nont, currentBack, indexI, indexJ)
            else:
                terminalsParents.append([nt,parsingTree.index(parsingTree[len(parsingTree)-1])])


def cky(words, grammar, nont):
    #####
    nwords = len(words)
    nnont = len(nont)

    ####
    score = np.zeros((nnont, nwords + 1, nwords + 1))
    back = [[[{} for j in range(nwords + 1)] for i in range(nwords + 1)] for m in range(nnont)]
    print "CKY\nscore shape:", score.shape
    print "words: ", nwords

    ####
    for w in range(0, nwords):  # para todas
        token = words[w]

        print token

        prod = grammar.productions(rhs=token)
        for p in prod:
            idx = nont.index(p.lhs())
            score[idx, w, w + 1] = p.prob()
            back[idx][w][w + 1] = [token]
        ### handle unaries
        added = True
        while added:
            added = False
            for pr in grammar.productions():
                # get only unaries nonterminals
                if len(pr.rhs()) == 1 and isinstance(pr.rhs()[0], Nonterminal):
                    bbidx = nont.index(pr.rhs()[0])
                    if score[bbidx][w][w + 1] > 0:
                        aa = pr.lhs()
                        bb = pr.rhs()
                        prob = pr.prob() * score[bbidx][w][w + 1]
                        if prob > score[nont.index(aa)][w][w + 1]:
                            score[nont.index(aa)][w][w + 1] = prob
                            back[nont.index(aa)][w][w + 1] = [bb[0]]
                            added = True

    for span in range(2, nwords + 1):
        for begin in range(0, nwords - span + 1):
            end = begin + span
            for split in range(begin + 1, end):

                # from datetime import datetime
                # print begin, split, end, str(datetime.now())

                for pr in grammar.productions():
                    # get only binaries
                    if len(pr.rhs()) == 2:
                        aa = pr.lhs()
                        bb = pr.rhs()[0]
                        cc = pr.rhs()[1]
                        aaidx = nont.index(aa)
                        bbidx = nont.index(bb)
                        ccidx = nont.index(cc)
                        prob = pr.prob() * score[bbidx][begin][split] * score[ccidx][split][end]
                        if prob > score[aaidx][begin][end]:
                            score[aaidx][begin][end] = prob
                            back[aaidx][begin][end] = [split, bb, cc]

                            ### handle unaries
                            added = True
                            while added:
                                added = False
                                for pr in grammar.productions():
                                    # from datetime import datetime
                                    # print "aqui", str(datetime.now())

                                    # get only unaries nonterminals
                                    if len(pr.rhs()) == 1 and isinstance(pr.rhs()[0], Nonterminal):
                                        bbidx = nont.index(pr.rhs()[0])
                                        aa = pr.lhs()
                                        bb = pr.rhs()
                                        prob = pr.prob() * score[bbidx][begin][end]
                                        if prob > score[nont.index(aa)][begin][end]:
                                            score[nont.index(aa)][begin][end] = prob
                                            back[nont.index(aa)][begin][end] = [bb[0]]
                                            added = True

    # print "nonterminals: ", nont
    # print "Score"
    # print score
    # print "Back"
    # print back

    global foundRoot
    global parsingTree
    global indexMaxScore
    global terminalsParents
    foundRoot = False
    parsingTree = []
    indexMaxScore = -1
    terminalsParents = []

    buildTree(score, back, nwords, nont, {}, -1, -1)
    # print "Candidate"
    # print parsingTree, type(parsingTree), type(parsingTree[0][0])
    return parsingTree




def convert(tree, index=0, answer=[]):
    # print answer, "|", tree
    size = len(tree.leaves())
    answer.append([Nonterminal(tree.label()), index, index + size])
    for child in tree:
        if isinstance(child, Tree):
            answer, index = convert(child, index, answer)
        else:
            index += 1
    return answer, index


def evaluate(candidate,gold):
    hitLabel = 0
    hitTag = 0

    for i in range(0,len(candidate)):
        if (i<len(gold)):
            if(candidate[i][0] == gold[i][0]):
                if((candidate[i][1] == gold[i][1]) & (candidate[i][2] == gold[i][2])):

                    hitLabel = hitLabel + 1
                    for j in range(0,len(terminalsParents)):
                        if i == terminalsParents[j][1]:
                            hitTag = hitTag + 1
    lblPrecision = hitLabel/len(candidate)
    lblRecal = hitLabel/len(gold)
    f1 = 0
    if lblRecal != 0:
        f1 = lblPrecision/lblRecal
    tagAccuracy = hitTag/len(terminalsParents)
    print "HIT LABEL",hitLabel
    print "LEN CANDIDATE", len(candidate)
    print "LEN GOLD" , len(gold)
    print "HIT TAG" , hitTag
    print "LEN WORDS " , len(terminalsParents)
    print
    print "LABEL PRECISION",lblPrecision
    print "LABEL RECALL", lblRecal
    print "F1", f1
    print "TAG ACCURACY", tagAccuracy







############ main ###########







#
# grammarstr = """S -> NP VP [0.9]
#          S -> VP [0.1]
#          VP -> V NP [0.5] | V [0.1] | V VP_V [0.3] | V PP [0.1]
#          VP_V -> NP PP [1.0]
#          NP -> NP NP [0.1] | NP PP [0.2] | N [0.7]
#          PP -> P NP [1.0]
#          N -> 'people' [0.5] | 'fish' [0.2] | 'tanks' [0.2] | 'rods' [0.1]
#          V -> 'people' [0.1] | 'fish' [0.6] | 'tanks' [0.3]
#          P -> 'with' [1.0]
#          """
# grammar = nltk.PCFG.fromstring(grammarstr)
#
# nont = set()
# for p in grammar.productions():
#     nont.add(p.lhs())
# nont = list(nont)
#
# treestr1 = '(S (NP (NP (N fish)) (NP (N people))) (VP (V fish) (NP (N tanks))))'
# treestr2 = '(S (NP (N people)) (VP (V fish) (PP (P with) (NP (N tanks)))))'
# treestr3 = '(S (NP (N people)) (VP (V fish) (NP (NP (N tanks) (PP (P with) (NP (N rods)))))))'
# treestr4 = '(S (NP (N people)) (VP (V fish)))'
#
# trees = [Tree.fromstring(treestr1), Tree.fromstring(treestr2), Tree.fromstring(treestr3), Tree.fromstring(treestr4)]
# sentences = ['fish people fish tanks', 'people fish with tanks', 'people fish tanks with rods', 'people fish']
#
# for sent in range(0, len(sentences)):
#     print "\n\nsentence: ", sentences[sent]
#     gold = convert(trees[sent], 0, [])[0]
#     estimate = cky(sentences[sent].split(), grammar, nont)
#     evaluate(estimate, gold)
#     print "    gold: ", gold
#     print "estimate: ", estimate
#





###############################





treeb = treebank.fileids()
shuffle(treeb)
limit = int(len(treeb)*.75)
# limit = int(len(treeb)*.15)
treeb1 = treeb[:limit]
treeb2 = treeb[limit:]

### setting the grammar
prod = Set([])
productions = []
for item in treeb1:
    for tree in treebank.parsed_sents(item):
        tree.collapse_unary(collapsePOS = False)
        tree.chomsky_normal_form(horzMarkov = 2)
        productions += tree.productions()

S = Nonterminal('S')
grammar = induce_pcfg(S, productions)

### setting nonterminals
nont = set()
for p in grammar.productions():
    nont.add(p.lhs())
nont = list(nont)

print "grammar:\nnumber of productions:", len(grammar.productions())
print "number of nonterminals:", len(nont)

### parsing
for item in treeb2:
    for tree in treebank.parsed_sents(item):

        from datetime import datetime
        print str(datetime.now())

        # get groundtruth
        gold = convert(tree, 0, [])[0]

        #get estimate
        sentence = tree.leaves()
        estimate = cky(sentence, grammar, nont)

        evaluate(estimate, gold)

        print "    gold: ", gold
        print "estimate: ", estimate
        print str(datetime.now())





















# #### cky do nltk
# from nltk.parse import ViterbiParser
# parser = ViterbiParser(pcfg)
# print "\n\n", list(parser.parse("fish people fish tanks".split()))
#
# s = '(S (NP-SBJ (NNP Mr.) (NNP Vinken)) (VP (VBZ is) (NP-PRD (NP (NN chairman)) (PP (IN of) (NP (NP (NNP Elsevier) (NNP N.V.)) (, ,) (NP (DT the) (NNP Dutch) (VBG publishing) (NN group)))))) (. .))'
# t = Tree.fromstring(s)
# print t, "\n----"
#
# tt = treebank.parsed_sents('wsj_0001.mrg')[1]
# print tt
# print "-----"
# print tt[0]
# print "-----"
# print tt[1]
# print "-----"
# print tt[1,0]
# print "-----"
# print tt[1,1]
# print "-----"
#
# print t==tt
