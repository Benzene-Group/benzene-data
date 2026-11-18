# Queue watch

Paid alert: £99 a month per watched site. Buy 5 sites and pay for 4 (every fifth site is free).

- `watchlist.json`: customers and what they watch. `sites` = exact NESO "Connection Site" names; `projects` = NESO project numbers (PRO-...). Optional `first_name` and `email`.
- After each new register, `scripts/refresh.py` runs `scripts/queue_watch.py` and writes alerts to `out/watch/<date>/`: one file per customer, plus `all/` with every changed site and `changes.json`.
- Alerts are drafts. The worker puts each one in Gmail as a draft to the customer's address; Ben sends.
