SELECT household_id
FROM household
WHERE tenure_months >= 12
  AND contract_status = 'month_to_month'
  AND support_contacts_90d >= 2
ORDER BY household_id;