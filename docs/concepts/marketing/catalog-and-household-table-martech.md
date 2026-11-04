# Catalog and Household Table Concepts in Telecom Marketing

## Household table (or customer / subscriber table)

In a large telecom this is the core customer data asset used for marketing. Each row typically represents a household or billing account (sometimes an individual subscriber). Columns hold the attributes marketing can target on:

- Tenure, contract end date, current products (internet speed tier, video package, mobile lines)
- Usage patterns (data consumption, streaming, voice)
- Geography (DMA, region, serviceability)
- Lifecycle stage, churn risk scores, propensity scores
- Prior campaign responses, suppression flags, credit or eligibility indicators

Marketing, analytics, and MarTech systems query this table (or a governed view of it) to build audiences, estimate reach, and activate segments. In practice it is usually a large, governed table or set of tables inside a customer data platform, data warehouse, or marketing cloud, not a raw operational database.

## Attribute catalog (or data dictionary / feature catalog / audience attribute catalog)

This is the governed metadata layer that describes which attributes from the household/customer data are approved for marketing use. It typically records:

- Business name and definition of the attribute
- Technical name and source
- Data type and allowed values or operators
- Privacy, sensitivity, or regulatory classification
- Whether the attribute is currently approved for targeting, personalization, or measurement
- Owner, refresh cadence, and any usage restrictions

The catalog exists so that marketers, campaign managers, and automated systems do not query arbitrary columns. It enforces consistency, compliance, and data quality. In a mature MarTech stack it often lives in a data catalog tool, a CDP’s attribute library, or a governed semantic layer that audience-building interfaces read from.

## How they relate in practice

Marketers or campaign systems consult the attribute catalog to see what they are allowed to use. They then build segment definitions (predicates) against the approved attributes. Those definitions are executed against the household/customer table (or a marketing-ready projection of it) to produce audience counts and exportable lists. The catalog is the control and documentation layer; the household table is the data that gets counted and activated. Without the catalog, targeting becomes inconsistent and risky; without the household data, the catalog has nothing to describe.
