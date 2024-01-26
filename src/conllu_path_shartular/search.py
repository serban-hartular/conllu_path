from __future__ import annotations

from typing import List

from conllu_path_shartular.search_evaluator import NodePathEvaluator
from conllu_path_shartular.expr_parser import parse_evaluator
from conllu_path_shartular.tree import Tree

class Match:
    def __init__(self, node : Tree, children : List[Match] = None):
        self.node = node
        self.next_matches = children if children is not None else []
        # self.metadata = {}

    def matches_level(self, depth) -> List[Match]:
        return Match.get_matches([self], depth)
    @staticmethod
    def get_matches(matches : List[Match], depth = 0) -> List[Match]:
        if depth < 0: return []
        if depth == 0:
            return matches
        match_list = []
        for match in matches:
            match_list += Match.get_matches(match.next_matches, depth - 1)
        return match_list

    def __str__(self):
        return 'Match(%s)' % str(self.node)
    def __repr__(self):
        return self.__str__()


class Search:
    def __init__(self, expr : str|List[NodePathEvaluator]):
        self.expr_src = None
        if isinstance(expr, str):
            self.expr_src = expr
            expr = parse_evaluator(expr)
        self.evaluator_sequence = expr
    def match(self, tree : Tree) -> List[Match]|List[Tree]:
        _match = Match(tree)
        if not Search._match_recursive(_match, self.evaluator_sequence):
            return []
        matches = _match.next_matches
        return matches if len(self.evaluator_sequence) > 0 else [m.node for m in matches]
    @staticmethod
    def _match_recursive(match : Match, evaluator_sequence : List[NodePathEvaluator]) -> bool:
        if not evaluator_sequence:
            return True
        if not evaluator_sequence[0].evaluate(match.node):
            return False
        match.next_matches = []
        for node in evaluator_sequence[0].matching_nodes:
            child = Match(node)
            if Search._match_recursive(child, evaluator_sequence[1:]):
                match.next_matches.append(child)
        return bool(match.next_matches)



