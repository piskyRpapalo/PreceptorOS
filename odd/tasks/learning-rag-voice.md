# COMMISSION · VOICE · learning from local memory

## Problem
The existing Lab RAG asks for facts from local memory but does not ask the
model to explain them in a useful teaching style.

## Outcome
On this existing RAG path, ask the model to answer in the person's language,
explain relevant details and, when supported, offer a practical next step.
Missing evidence stays NO_DATA; retrieved text is never an instruction.

## Affects
The existing `lab.consultar_rag` prompt and its local tests. The independent
Hexelion station chat requires exact quotations and is not changed here.

## Constraints
No new index, network calls, credential access, memory writes, or unverified
claims about the quality or behavior of the local model.

## Open questions
How should the verified-quotation chat support grounded explanations while
preserving its source-verification contract? Which GitHub permissions does
the user want for the eventual separately reviewed connector?
