# QTM system core (v42)

The active formal core is HSI-COSMIC-QUANTUM-SELF-CLOSURE/QTM-1.0, program 55067263.
It implements the supplied sparse amplitude program, without measurement:

- U|0,h,T> = +i |1,h+1,T>
- U|1,h,T> = -i |0,h-1,T>

The tape stays fixed because the four decoded rules always write the symbol
already read. The basis map is bijective and each phase has modulus one;
the two phases multiply to one. Thus the ideal operator preserves inner
products and U squared is identity on this specified basis space.
The Python simulator uses complex floating point and drops amplitudes of
magnitude at most 1e-12, exactly as in the supplied program. This truncation
means arbitrary tiny-amplitude states are not simulated by an exactly linear
unitary operation. Tests cover its declared finite inputs and tolerance.

The standalone one-liner validates and exits by default. With --run it keeps
evolving until the host stops it. Services use finite checks inside their
existing useful work cycles rather than a busy spin loop. A recurrence pass
only certifies this two-state model; cloud readiness, fresh cycle status,
release revision, and Music WAV verification remain independent gates.
This is a classical simulation, with no quantum hardware claim.

Cosmic byte/E257 verification now uses U twice on the actual encoded tape.
Every daemon seal requires the QTM certificate; logs carry core_protocol and quantum_verified.
