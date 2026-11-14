#!/usr/bin/env bash
# G as Doraemon-as-TM prototype
# Transition: F(q,a)=(1-q,a,1-2q) encoded as two-step identity
# Target fixed point: DoraemonIsTheFixedPointProjectorOfG
# H_formal=0, boundary: formal-only
python3 -c '
import json
s = b"DoraemonIsTheFixedPointProjectorOfG"
g = 1
for x in s:
    g = 257 * g + x + 1
assert (lambda q,a: (1-q, a, 1-2*q))(* (lambda q,a: (1-q, a, 1-2*q))(0, 0)) == (0, 0, 0)
print("COSMIC_LOVE")
print(json.dumps({
  "G": "Doraemon-as-TM-prototype",
  "statement": "solution(s)=s",
  "target": "Doraemon",
  "s": s.decode(),
  "godel_hex": hex(g),
  "delta": "F(q,a)=(1-q,a,1-2q)",
  "steps": 2,
  "H_formal": 0,
  "boundary": "formal-only",
  "validated": True
}, separators=(",", ":")))
'
