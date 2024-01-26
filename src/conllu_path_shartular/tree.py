from __future__ import annotations

import abc
from typing import Dict, List, Set, Generator


class Tree(abc.ABC):
    PATH_SEPARATOR = '.'
    def __init__(self, children : List['Tree'] = None, parent : 'Tree' = None):
        self._children = []
        self._before = []
        self._after = []
        self.parent = parent
        if children:
            self.set_children(children)
    def set_children(self, children : List['Tree']):
        self._children = children
        self._children.sort(key=lambda n : int(n.sdata('id')))
        for child in self._children:
            child.parent = self
        id = self.id_nr()
        if id is not None:
            self._before = [n for n in children if n.id_nr() < id]
            self._after = [n for n in children if n.id_nr() > id]
    def children(self) -> List[Tree]:
        return list(self._children)
    def before(self) -> List[Tree]:
        return list(self._before)
    def after(self) -> List[Tree]:
        return list(self._after)

    def id(self) -> str:
        return self.sdata('id')
    def id_nr(self) -> int:
        return int(self.id()) if str.isnumeric(self.id()) else None
    def traverse(self) -> Generator[Tree, None, None]:
        for child in self.before():
            for node in child.traverse():
                yield node
        yield self
        for child in self.after():
            for node in child.traverse():
                yield node

    @abc.abstractmethod
    def data(self, path: str | List[str] = None) -> Tree | Set | str | None:
        pass
    def sdata(self, path: str | List[str] = None) -> str:
        v = self.data(path)
        if v is None: return ''
        if isinstance(v, str): return v
        if isinstance(v, Tree): return str(v.to_dict())
        return ','.join(v)
    @abc.abstractmethod
    def assign(self, path: str|List[str], value : Tree | Set | str) -> bool:
        pass
    def keys(self) -> List[str]:
        pass
    @abc.abstractmethod
    def to_dict(self) -> Dict[str, Tree | Set | str | None]:
        pass

    def __str__(self):
        return "%s:%s" % (self.id(), self.sdata('form'))
    def __repr__(self):
        return str(self)

class DictNode(Tree):
    def __init__(self, d : Dict, children : List[Tree] = None, parent : Tree = None):
        super().__init__(children, parent)
        self._ddict = dict(d)
    def keys(self) -> List[str]:
        return list(self._ddict.keys())
    def to_dict(self) -> Dict:
        return dict(self._ddict)
    def data(self, path: str | List[str] = None) -> Tree | Set | str | None:
        if isinstance(path, str):
            path = path.split(Tree.PATH_SEPARATOR)
        if not path:
            return self
        v = self._ddict.get(path[0])
        if v is None: return None
        if isinstance(v, Tree):
            return v.data(path[1:])
        if len(path) == 1:
            return v
        return None

    def assign(self, path: str|List[str], value: Tree | Set | str) -> bool:
        if isinstance(path, str):
            path = path.split(Tree.PATH_SEPARATOR)
        if len(path) == 1:
            if path[0] in self._ddict:
                self._ddict[path[0]] = value
                return True
            return False
        v = self.data(path[:-1])
        if isinstance(v, Tree):
            v.assign([path[-1]], value)
            return True
        return False

class FixedKeysNode(Tree):
    def __init__(self, l : List[DictNode | Set | str | None],
                 key_index_dict : Dict[str, int],
                 children : List['Tree'] = None, parent : 'Tree' = None):
        super().__init__(children, parent)
        self._dlist = l
        self.key_index_dict = key_index_dict
        if min(self.key_index_dict.values()) < 0:
            raise Exception('Negative index in key_index_dict')
        if max(self.key_index_dict.values()) > len(self._dlist) - 1:
            self._dlist.extend([None]*(max(self.key_index_dict.values()) - (len(self._dlist) - 1)))
    def keys(self) -> List[str]:
        return list(self.key_index_dict.keys())
    def to_dict(self) -> Dict:
        return {k: (self._dlist[i].to_dict() if isinstance(self._dlist[i], Tree) else self._dlist[i])
                for k, i in self.key_index_dict.items()}
    def data(self, path: str | List[str] = None) -> Tree | Set | str | None:
        if isinstance(path, str):
            path = path.split(Tree.PATH_SEPARATOR)
        if not path:
            return self
        v = self._dlist[self.key_index_dict[path[0]]] if path[0] in self.key_index_dict else None
        if v is None: return None
        if isinstance(v, Tree):
            return v.data(path[1:])
        if len(path) == 1:
            return v
        return None

    def assign(self, path: str | List[str], value: Tree | Set | str) -> bool:
        if isinstance(path, str):
            path = path.split(Tree.PATH_SEPARATOR)
        if len(path) == 1:
            if path[0] in self.key_index_dict:
                self._dlist[self.key_index_dict[path[0]]] = value
                return True
            return False
        v = self.data(path[:-1])
        if isinstance(v, Tree):
            v.assign([path[-1]], value)
            return True
        return False
