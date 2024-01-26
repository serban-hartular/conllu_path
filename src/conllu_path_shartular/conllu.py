from __future__ import annotations

import typing
from io import StringIO
from typing import Dict, List, Generator
from conllu_path_shartular.exception import ConlluException
from conllu_path_shartular.tree import Tree, FixedKeysNode, DictNode
from conllu_path_shartular.sentence import Sentence

conllu_fields = ('id', 'form', 'lemma', 'upos', 'xpos', 'feats',
                 'head', 'deprel', 'deps', 'misc')
conllu_index_dict = {k:i for i, k in enumerate(conllu_fields)}
field_is_dict = ('feats', 'misc', 'deps')
EMPTY_FIELD = '_'
DICT_ITEM_SPLIT = '|'
KEY_VAL_SEP = {'feats': '=', 'misc' : '=', 'deps': ':'}
MANY_VALS_SEP = ','


def conllu_to_node(source : str, line_nr : int = None) -> FixedKeysNode:
    data_fields = source.strip().split('\t')
    if len(data_fields) != len(conllu_fields):
        raise ConlluException(source, 'Invalid nr of fields', line_nr)
    data_list = []
    for label, data_str in zip(conllu_fields, data_fields):
        if not data_str or data_str == EMPTY_FIELD:
            data_list.append(None)
        elif label in field_is_dict:
            #this field contains a dict
            items = data_str.split(DICT_ITEM_SPLIT)
            try:
                item_dict = {t[0]:set(t[1].split(MANY_VALS_SEP))
                             for t in (s.split(KEY_VAL_SEP[label], 1) for s in items)}
            except:
                raise ConlluException(data_str, 'Error splitting dict field', line_nr)
            data_list.append(DictNode(item_dict))
        else:
            data_list.append(data_str)
    return FixedKeysNode(data_list, conllu_index_dict)

def node_to_conllu(node : Tree) -> str:
    node = node.to_dict()
    data_list = []
    for label in conllu_fields:
        data = node.get(label)
        if isinstance(data, str):
            data = data if data else EMPTY_FIELD
        elif data is None:
            data = EMPTY_FIELD
        elif isinstance(data, Dict):
            data =\
                DICT_ITEM_SPLIT.join(
                    KEY_VAL_SEP[label].join([
                        k, MANY_VALS_SEP.join(v) if not isinstance(v, str) else v
                ])
            for k,v in data.items())
        else:
            raise ConlluException(str(data),
                    'Cannot transform %s item to conllu in %s' % (label, str(node)))
        data_list.append(data)
    return '\t'.join(data_list)

def sentence_to_conllu(sentence : Sentence) -> str:
    output = ''.join(['# %s\n' % m for m in sentence.meta]) if sentence.meta else ''
    output += '# sent_id = %s\n' % str(sentence.sent_id)
    output += '# text = %s\n' % str(sentence.text)
    for node in sentence.sequence:
        output += node_to_conllu(node) + '\n'
    output += '\n'
    return output

def iter_sentences_from_conllu(file : typing.TextIO | str) -> Generator[Sentence, None, None]:
    if isinstance(file, str):
        file = open(file, 'r', encoding='utf-8')
    line_nr = 0
    node_sequence = []
    meta_data = []
    special_data = {} # text, sent_id
    while True:
        line = file.readline()
        line_nr += 1
        if not line:
            break
        line = line.strip()
        if not line:
            # blank line - yield sentence if have sentence
            if node_sequence:
                if meta_data: # add metadata to sentence **kwargs
                    special_data.update({'meta':meta_data})
                sentence = Sentence(node_sequence, **(special_data))
                node_sequence = []
                meta_data = []
                special_data = {}  # text, sent_id
                yield sentence
            continue
        if line[0] == '#':# comment
            line = line[1:] # strip #
            if '=' in line: # check for sent_id, text
                k,arg = line.split('=',1)
                k, arg = k.strip(), arg.strip()
                if k in ('sent_id', 'text'):
                    special_data[k] = arg
                    continue
            meta_data.append(line.strip())
            continue
        node_sequence.append(conllu_to_node(line, line_nr))
    if node_sequence:
        if meta_data:  # add metadata to sentence **kwargs
            special_data.update({'meta': meta_data})
        yield Sentence(node_sequence, **(special_data))
    file.close()

def iter_sentences_from_conllu_str(conllu_str: str) -> Generator[Sentence, None, None]:
    return iter_sentences_from_conllu(StringIO(conllu_str))

