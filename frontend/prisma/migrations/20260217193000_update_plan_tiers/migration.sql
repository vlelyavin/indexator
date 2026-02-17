-- Normalize plan limits and pricing
UPDATE "Plan"
SET "name" = 'Free', "auditsPerMonth" = 5, "maxPages" = 10, "whiteLabel" = 0, "price" = 0
WHERE "id" = 'free';

UPDATE "Plan"
SET "name" = 'Pro', "auditsPerMonth" = 50, "maxPages" = 100, "whiteLabel" = 0, "price" = 20
WHERE "id" = 'pro';

UPDATE "Plan"
SET "name" = 'Agency', "auditsPerMonth" = 999999, "maxPages" = 500, "whiteLabel" = 1, "price" = 50
WHERE "id" = 'agency';
