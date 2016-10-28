import nltk
from nltk.grammar import Nonterminal
from nltk.corpus import treebank
from nltk import treetransforms
from nltk import induce_pcfg
from nltk import nonterminals
from nltk.parse import pchart

from nltk import PCFG

from sets import Set
from random import shuffle

import numpy as np
np.set_printoptions(suppress=True)

# treeb = treebank.fileids()
# shuffle(treeb)
# limit = int(len(treeb)*.75)
# limit = int(len(treeb)*.15)
# treeb1 = treeb[:limit]
# treeb2 = treeb[limit:]
#
# prod = Set([])
# productions = []
# for item in treeb1:
#     for tree in treebank.parsed_sents(item):
#         # tree.collapse_unary(collapsePOS = False)
#         tree.chomsky_normal_form(horzMarkov = 2)
#
#         # print len(tree.productions())
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
#
#





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

from nltk.parse import ViterbiParser
parser = ViterbiParser(pcfg)
# print list(parser.parse("fish fish tanks".split()))





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
    print "score shape: ", score.shape

    ####
    for w in range(0,nwords): # para todas
        token = words[w]
        prod = pcfg.productions(rhs=token)
        for p in prod:
            idx = nont.index(p.lhs())
            score[idx,w,w+1] = p.prob()
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
                                            prob = pr.prob() * score[bbidx][begin][end]
                                            if prob > score[nont.index(aa)][begin][end]:
                                                score[nont.index(aa)][begin][end] = prob
                                                added = True



    print "nonterminals: ", nont
    print score

cky("fish people fish tanks".split(), pcfg)
