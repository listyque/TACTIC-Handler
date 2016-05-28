input = [
    ('11013331', 'KAT'),
    ('9085267', 'NOT'),
    ('5238761', 'ETH'),
    ('5349618', 'ETH'),
    ('11788544', 'NOT'),
    ('962142', 'ETH'),
    ('7795297', 'ETH'),
    ('7341464', 'ETH'),
    ('9843236', 'KAT'),
    ('5594916', 'ETH'),
    ('1550003', 'ETH')
]

# sortkeyfn = key = lambda s: s[1]


def softkeyf(a):
    return a[1]

input = [('11013331', 'KAT'), ('9085267', 'NOT'), ('5238761', 'ETH'),
         ('5349618', 'ETH'), ('11788544', 'NOT'), ('962142', 'ETH'), ('7795297', 'ETH'),
         ('7341464', 'ETH'), ('9843236', 'KAT'), ('5594916', 'ETH'), ('1550003', 'ETH')]
# print(sortkeyfn(('11013331', 'KAT')))
print(softkeyf(('11013331', 'KAT')))
input.sort(key=softkeyf)

from itertools import groupby

result = []
for softkeyf, valuesiter in groupby(input, key=softkeyf):
    result.append(dict(type=softkeyf, items=list(v[0] for v in valuesiter)))

from pprint import pprint

pprint(result)
