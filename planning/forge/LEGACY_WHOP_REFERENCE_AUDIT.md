# LEGACY WHOP REFERENCE AUDIT — FORGE

Date: 2026-10-04
Source: dabiggestpoppa/larger-lab master

## Located
Historical MAD LABS Whop work is present on larger-lab/master:
- progress/PO-WHOP-STORE-TASK.md
- O2C-VAULT/journal_20260626T141000Z_po_whop_store_build.md
- O2C-VAULT/journal_20260626T142000Z_pm2_whop_build.json
- tests/log_po_whop.py
- tests/pm2_whop_verify.py
- whop-landing gitlink at commit b56fb2ab7eefdc3585e923c39456c943ac88b4b5

The gitlink target is not materialized as a normal tree in larger-lab and its referenced commit is not resolvable as a larger-lab commit. Treat the historical journals/config specification as verified reference; do not pretend the landing-page source has been recovered.

## Historical store architecture
The old design separated:
products/
  consultations
  digital
  bootcamps
  software
community/tiers
branding/config
payments/config
integrations/config
store.json

It modeled active/coming-soon/in-development states, Whop as primary commerce, Stripe/PayPal fallback concepts, Discord/Calendly integrations and a master store manifest.

## What survives into FORGE
1. Commerce is a replaceable adapter, not the product core.
2. Product catalog, plans/tiers, entitlements and delivery capabilities should be first-class internal records.
3. Whop identifiers belong in provider mappings, not domain model primary keys.
4. Store status and offering lifecycle are explicit.
5. Community/software/research can be separately entitled.
6. Verification must test commerce events against internal entitlement state.
7. Brand/store config belongs outside code where possible.

## What does NOT transfer blindly
- MAD LABS branding/products/prices.
- placeholder URLs.
- old payment fallback assumptions.
- old OCE observer/governance verification as proof of Whop API correctness.
- any historical Whop API contract without current implementation validation.
- the old landing-page gitlink as source truth.

## FORGE commerce doctrine
GLX FORGE owns:
user/account
plan
product
entitlement
license
feature/exposure policy
access audit.

Whop owns only provider-side:
checkout/payment/subscription/customer state and provider event IDs.

Whop -> verified webhook/event adapter -> entitlement reconciler -> FORGE access policy.

Loss/replacement of Whop must not destroy CEREBUS identity, canonical corpus, user/license records or internal entitlement semantics.
