# App text and leitmotif census

Date: 2026-10-21. Base: `58ba72563c901845df8772ddabd23b6810fcfa5c`. Scope: repository text tables and deterministic locally generated leitmotifs; no source files changed.

## Text tables

`textos.py:29,38-40,52-391` declares English as the default, nine languages, and the English/Spanish base tables.

`textos.py:394-397` merges the seven additional translations from `textos_lenguas.py` at import time.

`textos_lenguas.py:18-25` records translation provenance and native-review status as pending.

Measured runtime result: 9/9 languages contain the same 97 keys; no missing or extra keys were observed.

| Language | Strings | UTF-8 bytes | Canonical table SHA-256 |
|---|---:|---:|---|
| en | 97 | 5,068 | `3b1bd0fe5d53c8345e8f5d78c8e46985fadedfe9a5eb563543de840c692d0600` |
| es | 97 | 5,296 | `4c47f7c459e614d4cfcb69c93c7ac0efdf8ecd089d980d012c0f4504312ec001` |
| fr | 97 | 5,780 | `3438518d9ef312331c471e7fe4c875dfeab9c77242d0d9bf8d25b3805d07f7bc` |
| pt | 97 | 5,297 | `4559ce5514b61b873cacfe49a078d7e887bd2617ef35eebad2aa8df6a18ba9a9` |
| it | 97 | 5,341 | `9771d91059665d808d633499c289abe66ab9dafa6154d6ac384de599d983f649` |
| de | 97 | 5,917 | `9f053625d0bffcfde6de37f2f3a90b80ce37e8916b2c1c3d6eb887f455ce5ea8` |
| ru | 97 | 8,745 | `a1884451923fe3937286f38a9dba2719c394e24743aa366c4709bb0520607b3e` |
| el | 97 | 9,479 | `64b60a0f3408bbaea4fd516078ff2cde9c28f66da603da9486162af914286db6` |
| ar | 97 | 6,724 | `8c5552cbcd07f96829f1e4ad58791154b5469f0f74af722945756151b261bd3e` |

Hashes use UTF-8 JSON with sorted keys and compact separators; they identify each expanded language table, not the source file.

## Leitmotifs

`generar_leitmotivs.py:31-42` defines six room recipes at 22,050 Hz for 2.5 seconds; `:51-90` derives samples from the room name and recipe; `:94-124` writes WAV files only when called.

`voz.py:200-214` resolves the same six room names to generated files and returns no path when one is absent.

Two separate Python 3.14.4 processes generated all six files into disposable temporary directories on Linux 7.0.0-38-generic x86_64 (16 logical CPUs). Every file was 110,294 B and all six SHA-256 digests matched across processes; total output was 661,764 B per run.

| Room | Output SHA-256 |
|---|---|
| 1 | `c6f497a1648423fc385f130c7374de3bd9ae1274fa3d0ac6e9abaee0a6b8d22b` |
| 2 | `25a3279c8511b9ba1d295b67b799d342da0c9596f874492e85bcd53cf0afe4a4` |
| 3 | `030eb42c62826c530f4748d2561aec8d787d56020498c63999ed50e24a6e8a4a` |
| 4 | `08367233fbfa527c26dddf37c5b7bb29758bb290978121be7a6b74a904c81ac4` |
| 5 | `d5bafbfecccf2f1a21cd013fa152cbe7b47ed86a1d73267584643c2f9bbda56e` |
| 6 | `97fc5cf09873decef8d4eeff7cff3f08d48231c7e62087507da19417b1d1bce3` |

`test_idioma.py` exercises the user-facing language flow and translation completeness; `test_leitmotivs.py:172-196` checks WAV structure and name agreement with the playback resolver.

## Limits and next measurement

Native-speaker review of the seven added translations remains `NO_DATA`: the repository marks it pending at `textos_lenguas.py:18-25`.

Playback through an installed voice device and physical listening quality remain `NO_DATA`: this census hashes generated WAV files and does not play them.

The next useful optimization is to keep this two-process digest comparison as a release check for recipe changes; baseline is six matching digests per run pair, and a changed digest must show an intentional recipe change.
