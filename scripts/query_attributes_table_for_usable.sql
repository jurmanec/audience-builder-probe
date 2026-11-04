SELECT usable, count(*)
FROM attribute
GROUP BY usable
ORDER BY usable DESC;