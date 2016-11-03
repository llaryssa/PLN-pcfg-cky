import nltk
from nltk.grammar import Nonterminal
from nltk.corpus import treebank
from nltk import treetransforms
from nltk import induce_pcfg
from nltk import nonterminals
from nltk.parse import pchart
from  nltk.tree import Tree

from nltk import PCFG

from sets import Set
from random import shuffle

import numpy as np
np.set_printoptions(suppress=True)

treeb = treebank.fileids()
print(treebank.parsed_sents('wsj_0001.mrg')[0])




# shuffle(treeb)
# limit = int(len(treeb)*.75)
# limit = int(len(treeb)*.15)
# treeb1 = treeb[:limit]
# treeb1 = treeb[:1]
# treeb2 = treeb[limit:]
#
# prod = Set([])
# productions = []
# for item in treeb1:
#     for tree in treebank.parsed_sents(item):
#         # tree.collapse_unary(collapsePOS = False)
#         tree.chomsky_normal_form(horzMarkov = 2)
#
#         print treebank.words(item)
#         print type(tree)
#
#         productions += tree.productions()
#
#         for t in tree.productions():
#             prod.add(t)
#
#
# S = Nonterminal('S')
# grammar = induce_pcfg(S, productions)
# # print grammar
#
#
# print len(grammar.productions()), len(prod)






str = """S -> NP VP [0.9]
         S -> VP [0.1]
         VP -> V NP [0.5] | V [0.1] | V VP_V [0.3] | V PP [0.1]
         VP_V -> NP PP [1.0]
         NP -> NP NP [0.1] | NP PP [0.2] | N [0.7]
         PP -> P NP [1.0]
         N -> 'people' [0.5] | 'fish' [0.2] | 'tanks' [0.2] | 'rods' [0.1]
         V -> 'people' [0.1] | 'fish' [0.6] | 'tanks' [0.3]
         P -> 'with' [1.0]
         """
pcfg = nltk.PCFG.fromstring(str)
print pcfg

for p in pcfg.productions():
    print p.lhs(), p.rhs(), p.prob()


print type(pcfg.productions()[0])

print "------------"

print pcfg.productions(lhs=Nonterminal('V'), rhs='people')


print "------------"

foundRoot = False
parsingTree = ""
indexMaxScore = -1;

def buildTree(score, back, nwords, nont, currentBack, indexI, indexJ):
    global parsingTree
    global foundRoot
    global indexMaxScore

    if not foundRoot:
        maxScore = -1;

        for i in range(0, len(nont)):
            if score[i][0][nwords] > maxScore:
                maxScore = score[i][0][nwords]
                indexMaxScore = i
        foundRoot = True
        top = nont[indexMaxScore]
        currentBack = back[indexMaxScore][0][nwords]
        parsingTree = parsingTree + "{}-(0:{})".format(top,nwords)

        buildTree(score,back,nwords,nont,currentBack, 0, nwords)
    else:
        if len(currentBack) == 3:

            split = currentBack[0]
            firstNT = currentBack[1]
            firstNTIndex = nont.index(firstNT)
            secondNT = currentBack[2]
            secondNTIndex = nont.index(secondNT)

            parsingTree = parsingTree + ", {}-({}:{})".format(firstNT, indexI, split)
            currentBack = back[firstNTIndex][indexI][split];
            buildTree(score, back, nwords, nont, currentBack, indexI, split)

            parsingTree = parsingTree + ", {}-({}:{})".format(secondNT, split, indexJ)
            currentBack = back[secondNTIndex][split][indexJ];
            buildTree(score, back, nwords, nont, currentBack, split, indexJ)


        elif len(currentBack) == 1:

            nt = currentBack[0]
            if nt in nont:
                ntIndex = nont.index(nt)



                parsingTree = parsingTree + ", {}-({}:{})".format(nt, indexI, indexJ)
                currentBack = back[ntIndex][indexI][indexJ];
                buildTree(score, back, nwords, nont, currentBack, indexI, indexJ)

            else: #terminal

                print nt






def cky(words, grammar):
    print "\n====== CKY ======"
    #### could be done before
    nont = set()
    for p in grammar.productions():
        nont.add(p.lhs())
    nont = list(nont)

    #####
    nwords = len(words)
    nnont = len(nont)

    ####
    score = np.zeros((nnont, nwords+1, nwords+1))
    back = [[[{} for j in range(nwords + 1)] for i in range(nwords + 1)] for m in range(nnont)]

    print "score shape: ", score.shape


    ####
    for w in range(0,nwords): # para todas
        token = words[w]
        prod = pcfg.productions(rhs=token)
        for p in prod:
            idx = nont.index(p.lhs())
            score[idx,w,w+1] = p.prob()
            back[idx][w][w+1] = [token]
        ### handle unaries
        added = True
        while added:
            added = False
            for pr in grammar.productions():
                # get only unaries nonterminals
                if len(pr.rhs()) == 1 and isinstance(pr.rhs()[0], Nonterminal):
                    bbidx = nont.index(pr.rhs()[0])
                    if score[bbidx][w][w+1] > 0:
                        aa = pr.lhs()
                        bb = pr.rhs()
                        prob = pr.prob() * score[bbidx][w][w+1]
                        if prob > score[nont.index(aa)][w][w+1]:
                            score[nont.index(aa)][w][w+1] = prob
                            back[nont.index(aa)][w][w+1] = [bb[0]]
                            added = True

    for span in range(2,nwords+1):
        for begin in range(0, nwords-span+1):
            end = begin + span
            for split in range(begin+1, end):
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



    print "nonterminals: ", nont
    print "Score"
    print score
    print "Back"
    print back

    buildTree(score,back,nwords,nont,{},-1,-1)
    print parsingTree, type(parsingTree)

cky("fish people fish tanks".split(), pcfg)







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



st = '(S (NP (NP (N fish)) (NP (N people))) (VP (V fish) (NP (N tanks))))'
tree = Tree.fromstring(st)
print tree

def convert(tree, index=0, parsing=[]):
    size = len(tree.leaves())
    parsing.append([tree.label(),index,index+size])
    for child in tree:
        if isinstance(child, Tree):
            pars, index = convert(child, index, parsing)
        else:
            index += 1
    return parsing, index


parsing, index = convert(tree)
print parsing
