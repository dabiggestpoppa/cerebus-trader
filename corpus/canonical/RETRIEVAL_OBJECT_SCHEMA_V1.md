# CEREBUS CANONICAL RETRIEVAL OBJECT SCHEMA V1

object_id:
object_type: MODEL | CLAIM | EVIDENCE | SETUP | DOCTRINE | TERM | LINEAGE
canonical_version:
title:
market_scope:
layer:
status:
exposure_class:
parent_ids:
source_artifact_ids:

## Retrieval text
A concise canonical statement generated from the authoritative object.

## Structured fields
terms:
aliases:
clocks:
states:
events:
levels:
metrics:
sample_n:
period:
implementation_ids:

## Routing metadata
beginner_weight:
operator_weight:
researcher_weight:
actionable: true|false
requires_setup_card: true|false
requires_evidence_card: true|false

## Leakage metadata
contains_internal_method: true|false
contains_code: true|false
max_quote_scope:

## Conflict metadata
supersedes_ids:
contradicts_ids:
generation:

## Embedding rule
Embed the canonical retrieval text and safe aliases, not entire raw artifacts by default.

## Structured-first rule
For exact numbers, levels, statuses, versions and relationships, resolve structured fields/registry before semantic similarity.

## Provenance rule
Every retrieval object must route back to at least one canonical object and source/provenance record.
