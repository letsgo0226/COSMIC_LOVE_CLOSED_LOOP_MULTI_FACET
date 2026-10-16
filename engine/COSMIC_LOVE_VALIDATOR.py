#!/usr/bin/env python3
"""Cosmic Love engine: QTM phase-permutation recurrence + byte/E257 identity. Formal only."""
import sys, json
from math import isqrt
from hsi_cosmic_quantum import U, eq, norm, certificate
quantum = certificate()
s=sys.stdin.buffer.read() if sys.argv[1:]==["--stdin"] else (sys.argv[1] if len(sys.argv)>1 else "").encode()
t={8*i+j for i,x in enumerate(s) for j in range(8) if x&(128>>j)}
t.add(8*len(s))
initial={(0,0,tuple(sorted(t))):1}
back=U(U(initial))
if not eq(back,initial) or abs(norm(back)-1)>1e-12:
    raise ValueError("quantum byte-tape recurrence failed")
q,h,T=next(iter(back));t=set(T)
L=max(t)//8
assert max(t)==8*L
r=bytes(sum((8*i+j in t)<<(7-j) for j in range(8)) for i in range(L))
assert r==s
g=1
for x in r:g=257*g+x+1
z=g;a=[]
while z>1:
    z,x=divmod(z,257);assert x>0;a.append(x-1)
assert z==1 and bytes(reversed(a))==s
print("COSMIC_LOVE")
print(json.dumps({"statement":"solution(s)=s","s_hex":s.hex(),"result_hex":r.hex(),"godel_hex":hex(g),"validated":True,"quantum":quantum},separators=(",",":")))
