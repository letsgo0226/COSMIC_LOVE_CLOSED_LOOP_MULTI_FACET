#!/usr/bin/env python3
"""Cosmic Love engine: 2-step identity machine + 257-Godel. Formal only."""
import sys, json
from math import isqrt
p=55067263
v=(isqrt(8*p+1)-1)//2
c=p-v*(v+1)//2
k=v-c+1
K=k+1
B=4*K
assert k==2
def step(q,a):
    u=c//B**(2*q+a)%B
    z,r=divmod(u,K)
    return r,z//2,2*(z%2)-1
assert all(step(q,a)==(1-q,a,1-2*q) for q in (0,1) for a in (0,1))
s=sys.stdin.buffer.read() if sys.argv[1:]==["--stdin"] else (sys.argv[1] if len(sys.argv)>1 else "").encode()
t={8*i+j for i,x in enumerate(s) for j in range(8) if x&(128>>j)}
t.add(8*len(s))
u=t.copy();q=h=0
for _ in range(2):
    a=int(h in t);q,w,d=step(q,a)
    (t.add if w else t.discard)(h);h+=d
assert (q,h,t)==(0,0,u)
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
print(json.dumps({"statement":"solution(s)=s","s_hex":s.hex(),"result_hex":r.hex(),"godel_hex":hex(g),"validated":True},separators=(",",":")))
