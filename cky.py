import nltk
from nltk.grammar import Nonterminal
from nltk.corpus import treebank
from nltk import treetransforms
from nltk import induce_pcfg
from nltk import nonterminals
from nltk.parse import pchart

from sets import Set
from random import shuffle

treeb = treebank.fileids()
shuffle(treeb)
limit = int(len(treeb)*.75)
limit = int(len(treeb)*.25)
treeb1 = treeb[:limit]
treeb2 = treeb[limit:]

prod = Set([])
productions = []
for item in treeb1:
    for tree in treebank.parsed_sents(item):
        # tree.collapse_unary(collapsePOS = False)
        tree.chomsky_normal_form(horzMarkov = 2)

        # print len(tree.productions())

        productions += tree.productions()

        for t in tree.productions():
            prod.add(t)


S = Nonterminal('S')
grammar = induce_pcfg(S, productions)
# print grammar

print(prod)

print len(grammar.productions()), len(prod)

# for reg in grammar.productions()[:20]
#     print reg, "***"
