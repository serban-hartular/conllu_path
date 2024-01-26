from __future__ import annotations

from collections import defaultdict
from typing import List

from conllu_path_shartular.tree import Tree
from conllu_path_shartular.search import Search, Match

class Sentence:
    def __init__(self, node_sequence : List[Tree], **kwargs):
        self.sequence = node_sequence
        self.sent_id = kwargs.get('sent_id')
        self.text = kwargs.get('text')
        self.meta = kwargs.get('meta')
        self._id_dict = {n.sdata('id'):n for n in self.sequence}
        self.root = None
        self.sanity_comment = ''
        self._is_good = self.sanity_check()
        if self._is_good:
            self.build_tree()

    def sanity_check(self) -> bool:
        ids = [n.id() for n in self.sequence]
        if not ids:
            self.sanity_comment = "sentence cannot be empty"
            return False
        if '' in ids:
            self.sanity_comment = "every node must have an id"
            return False
        if len(ids) != len(set(ids)):
            self.sanity_comment = "ids must be unique"
            return False
        num_ids = [int(id) for id in ids if str.isnumeric(id)]
        if list(range(1, len(num_ids)+1)) != num_ids:
            self.sanity_comment = "node ids must start with 1 and be successive"
            return False
        heads = [n.sdata('head') for n in self.sequence if n.id_nr() is not None]
        if '' in heads:
            self.sanity_comment = "can't build a tree without heads"
            return False
        roots = [h for h in heads if h == '0']
        if len(roots) != 1:
            self.sanity_comment = "tree must have exactly one root"
            return False
        heads = set(roots)
        heads.remove('0')
        num_ids = set(str(id) for id in num_ids)
        if not heads.issubset(num_ids):
            self.sanity_comment = "heads must point to existing nodes"
            return False
        return True

    def build_tree(self):
        children_dict = defaultdict(list)
        for node in self.sequence:
            if node.id_nr() is None:
                continue
            head = node.sdata('head')
            if head == '0':
                self.root = node
            else:
                children_dict[head].append(node)
        for head_id, children in children_dict.items():
            self._id_dict[head_id].set_children(children)

    def __bool__(self):
        return self._is_good
    def get_node(self, id : str) -> Tree:
        return self._id_dict.get(id)

    def search(self, src: str|Search) -> List[Tree]|List[Match]:
        if isinstance(src, str):
            src = Search(src)
        return src.match(self.root)

    def __str__(self):
        s = 'Sentence('
        if self.sent_id:
            s += 'sent_id=%s,' % self.sent_id
        text = self.text if self.text else ' '.join([n.sdata('form') for n in self.sequence])
        s += '"%s")' % text
        return s

    def __repr__(self):
        return str(self)
