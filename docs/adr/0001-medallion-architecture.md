# Adopt medallion architecture (bronze/silver/gold) as the layer vocabulary

We organize the warehouse into three schemas named `bronze`, `silver`, and `gold`. Bronze holds immutable raw API payloads; silver holds cleaned, typed, deduplicated models; gold holds conformed dimensional marts. Earlier drafts used "raw/iron/copper"; we rejected that in favor of the industry-recognized medallion names so the project reads immediately to reviewers and maps cleanly onto dbt project conventions.
