Betting process looks like such:

- User logs on
- User finds team to bet on
- User places bet through UI
Creates following:
```
bets {
  better => user_id,
  match => match_id,
  state => offered,
  team => 0
}
```
```
item ... {
  item => item_info,
  account => null,
  owner => user_id,
  bet => bet_id,
  locked => false
}
```
- Placed into redis queue
- Bot sends trade offer
- User accepts trade offer
```
bets {
  state => accepted
}
```
- Match is played
- User wins bet
- Item draft happens
```
bets {
  state => won
}
```
- Trades sent
- :)
