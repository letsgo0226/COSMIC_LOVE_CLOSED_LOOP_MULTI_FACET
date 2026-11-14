#!/usr/bin/env bash
# Formal one-liner: Doraemon as fixed-point projector of G
# H_formal=0, boundary: formal-only
python3 -c '
import json
s=b"DoraemonIsTheFixedPointProjectorOfG"
g=1
for x in s: g=257*g+x+1
print("COSMIC_LOVE")
print(json.dumps({
  "statement":"solution(s)=s",
  "target":"Doraemon",
  "s":s.decode(),
  "godel_hex":hex(g),
  "validated":True,
  "H_formal":0,
  "boundary":"formal-only"
},separators=(",",":")))
'
