# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

delegated: static HTML, CSS and JavaScript, served by Python's built-in HTTP server. This keeps the demo offline-first and dependency-free, matching the prototype constraint.

## Users

Primary users are cooperative financial institution agents, compliance officers and CIF hackathon jurors. Agents need to screen clients and transactions quickly at a modest branch workstation. Compliance officers need traceable decisions and proof that sanctions lists are current.

## Product Purpose

SentinelleCoop demonstrates an offline-first LBC/FT/FP screening workflow for West African cooperatives. Success means a jury can see, in a few minutes, how the solution detects name variants, consolidates client accounts, flags suspicious behavior and produces an auditable compliance trail.

## Positioning

The product's differentiating mechanism is a West African phonetic matching engine combined with local execution and compliance proof. It is not a generic AML dashboard: it is calibrated for UEMOA names, intermittent connectivity and modest IT resources.

## Operating Context

The demo is prepared for the CIF DigiCoop-WA+ Hackathon National d'Innovation in Ouagadougou, 4-6 September 2026. It supports Theme 01: client filtering and LBC/FT/FP information-system compliance. Demonstration data is synthetic except for the existing prototype benchmark based on the UN consolidated sanctions list.

## Capabilities and Constraints

Core capabilities to preserve: client screening, blocking and informative alerts, multi-account consolidation, transaction monitoring, compliance review, audit trail and report generation. Constraints: must run locally, avoid paid APIs, avoid external package installation, and make synthetic data clearly recognizable as demo data.

## Brand Commitments

Product name: SentinelleCoop. Voice: precise, sober, regulatory and field-oriented. The strongest proof points are offline operation, West African name matching and demonstrable "sans delai" list freshness.

## Evidence on Hand

Existing prototype: `sentinellecoop/`.
Submission package: `soumission/`.
Benchmark output: `data/benchmark_resultats.txt`.
Project note: `soumission/02-NOTE-PRESENTATION-SOLUTION.md`.
Terms of reference: `tdr-appel-a-candidatures-global-hackathon-cif-digicoop-wa-2026.md`.

## Product Principles

1. Show the compliance workflow, not only the algorithm.
2. Prove with measured outputs and audit traces.
3. Design for branch reality: low bandwidth, modest hardware, short attention.
4. Keep the prototype honest: label simulated data and name unimplemented production work.
5. Make the winning demo easy to rehearse in under five minutes.

