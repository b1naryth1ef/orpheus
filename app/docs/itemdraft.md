## Helpful Queries:

#### Bets joined on their item_count:
```sql
SELECT betters.*, count(items.better) as num_items FROM betters WHERE mid=$MATCH_ID AND tid=$TEAM_ID LEFT JOIN items ON (betters.id = items.better) GROUP BY betters.id ORDER BY num_items;
```

#### Calculate average amount of money 'stolen' for a draft
```sql
SELECT sum(betters.needed) / count(betters) as average_stolen FROM betters WHERE mid=$MATCH_ID AND tid=$TEAM_ID;
```

#### Grab items leftover from bet
```sql
SELECT sum(value) as value, count(*) as count FROM items WHERE mid=$MATCH_ID AND tid=$TEAM_ID AND better IS NULL;
```
