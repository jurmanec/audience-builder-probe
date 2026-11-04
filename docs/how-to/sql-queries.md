
## Attributes Catalog Table

### query for usable
```sql
SELECT usable, count(*)
FROM attribute
GROUP BY usable
ORDER BY usable DESC;
```

## Households Table

### Predicate queries
At-risk renewal: tenure at least 12 months, month-to-month, and at least two support contacts in 90 days.
```sql
SELECT household_id
FROM household
WHERE tenure_months >= 12
  AND contract_status = 'month_to_month'
  AND support_contacts_90d >= 2
ORDER BY household_id;
```

Heavy-use upgrade in one region: region `north`, internet `none` or `basic`, and at least 500 GB in 30 days.
```sql
SELECT count(*)
FROM household
WHERE region = 'north'
  AND internet_tier IN ('none', 'basic')
  AND data_gb_30d >= 500;
```

Lapsed video offer: video subscribed, autopay off, and at least 180 days since the last offer.
```sql
SELECT count(*)
FROM household
WHERE video_subscribed = true
AND autopay = false
AND days_since_last_offer >= 180;
```
