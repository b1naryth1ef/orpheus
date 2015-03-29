/*
    CSGO Emporium Backend Database Schema
*/

/*
  Tracks migrations in the database
*/

CREATE TABLE schemaversion (
  version INT PRIMARY KEY
);

INSERT INTO schemaversion VALUES (0);


/*
  Represents a cached item price in the database
*/

CREATE TABLE itemprices (
  id      SERIAL PRIMARY KEY,
  name    text,
  price   numeric,
  updated timestamp
);

CREATE INDEX on itemprices (name);


/*
  Represents a single item in the database

  owner: steamid, can be null
  price: cached price, can be null
*/

CREATE TYPE item_state AS ENUM ('UNKNOWN', 'EXTERNAL', 'INTERNAL', 'LOCKED');

CREATE TABLE items (
  id           numeric PRIMARY KEY,
  name         text NOT NULL,
  owner        varchar(255),
  image        varchar(1024),
  class_id     integer NOT NULL,
  instance_id  integer NOT NULL,
  price        decimal,
  state        item_state,
  meta         jsonb
);

CREATE INDEX ON items (name);
CREATE INDEX ON items (class_id, instance_id);

/*
  REPRESENTS FUCKING STEAM SUCKING
*/

CREATE TYPE return_state AS ENUM ('PENDING', 'RETURNED', 'LOCKED');

CREATE TABLE returns (
  id         SERIAL PRIMARY KEY,
  state      return_state NOT NULL,
  match      integer references matches(id),
  user       integer references users(id),
  trade      integer references trades(id),
  item_type  integer references itemprices(id),
  item_id    numeric
);

/*
  Represents a single user in the system
    steamid: the users steamid
    email: the users email (if set)
    active: a boolean value if the user is active
    join_date: the date the user joined
    last_login: the last time the user logged in
    ugroup: the users group (enum)
    settings: the users settings (json)
*/

CREATE TYPE user_group AS ENUM ('NORMAL', 'MODERATOR', 'ADMIN', 'SUPER');

CREATE TABLE users (
  id           SERIAL PRIMARY KEY,
  steamid      varchar(255) NOT NULL UNIQUE,
  email        varchar(255) UNIQUE,
  trade_token  varchar(32) UNIQUE,
  active       boolean,
  join_date    timestamp,
  last_login   timestamp,
  ugroup       user_group,
  settings     jsonb
);

CREATE INDEX ON users USING btree (id);
CREATE INDEX ON users (steamid);


/*
  Represents a single steam bot-account
    steamid: the bots steamid
    username: the bots steam username (NOT profile name)
    password: the bots AES-256-CTR encrypted password
    sentry: the bots AES-256-CTR encrypted sentry SHA
    status: the bot status (enum)
    last_activity: the last time something happened on this bot
    active: whether this bot can be used
*/

CREATE TYPE bot_status AS ENUM ('NEW', 'COOLDOWN', 'NEEDGAME', 'AVAIL', 'USED', 'INVALID');

CREATE TABLE bots (
    id             SERIAL PRIMARY KEY,
    steamid        varchar(255),
    username       varchar(255),
    password       varchar(255),
    profilename    varchar(255),
    apikey         varchar(32),
    token          varchar(32),
    sentry         bytea,
    status         bot_status,
    arbiter        integer,
    inventory      numeric[],
    last_activity  timestamp,
    active         boolean
);

CREATE INDEX ON bots USING GIN (inventory);


/*
  Represents crawled steam_guard_codes
    email: the email the steam_guard_code was sent too
    username: the username the steam_guard_code is for
    code: the actual code
*/

CREATE TABLE steam_guard_codes (
    id        SERIAL PRIMARY KEY,
    email     varchar(255),
    username  varchar(255),
    code      varchar(5)
);


/*
  Represents a game on which matches can be played
    name: the game name to be used in titles/etc
    meta: holds game metadata (links, rules, etc)
    appid: the steam appid
    view_perm: the user group that can view this
    active: whether this is active
    created_by: user created by
    created_at: when this was created
*/

CREATE TABLE games (
    id          SERIAL PRIMARY KEY,
    name        varchar(255) NOT NULL,
    meta        jsonb,
    appid       integer UNIQUE NOT NULL,
    view_perm   user_group,
    active      boolean,
    created_by  integer REFERENCES users(id),
    created_at  timestamp
);


CREATE TYPE event_type AS ENUM ('EVENT', 'SEASON');

CREATE TABLE events (
  id          SERIAL PRIMARY KEY,
  name        varchar(255) NOT NULL,
  website     varchar(255) NOT NULL,
  league      varchar(255) NOT NULL,
  logo        varchar(255) NOT NULL,
  splash      varchar(255) NOT NULL,
  streams     varchar(256)[],
  games       integer[],
  etype       event_type,
  start_date  timestamp,
  end_date    timestamp,
  active      boolean
);

/*
  Represents a team
*/

CREATE TABLE teams (
  id          SERIAL PRIMARY KEY,
  tag         varchar(24) UNIQUE,
  name        text,
  logo        text,
  meta        jsonb,
  created_by  integer REFERENCES users(id),
  created_at  timestamp
);


/*
  Represents a match played on a game for which there is a result and bets
    game: the game reference
    teams: a list of NON-FOREIGN references to teams
    players: a list of NON-FOREIGN references to users
    meta: metadata (e.g. media, streams)
    match_date: when this match is actually being played
    public_date: when this match goes public
    view_perm: what user group can view this
    active: whether this is active
    created_by: user created by
    created_at: when this was created
*/

CREATE TYPE match_state AS ENUM ('OPEN', 'WAITING', 'RESULT', 'LOCKED', 'CLOSED', 'COMPLETED');
CREATE TYPE match_item_state AS ENUM ('OPEN', 'LOCKED', 'RETURNED', 'DISTRIBUTED');

CREATE TABLE matches (
    id               SERIAL PRIMARY KEY,
    state            match_state NOT NULL,
    itemstate        match_item_state NOT NULL,
    event            integer REFERENCES events(id),
    game             integer REFERENCES games(id),
    teams            integer[],
    meta             jsonb,
    results          jsonb,
    max_value_item   decimal,
    max_value_total  decimal,
    match_date       timestamp,
    public_date      timestamp,
    items_date       timestamp,
    view_perm        user_group,
    active           boolean,
    created_by       integer REFERENCES users(id),
    created_at       timestamp,
    results_by       integer REFERENCES users(id),
    results_at       timestamp
);


/*
  Represents a bet placed on a match
*/

CREATE TYPE bet_state AS ENUM ('NEW', 'CANCELLED', 'CONFIRMED', 'WON', 'LOST');

CREATE TABLE bets (
    id          SERIAL PRIMARY KEY,
    better      integer REFERENCES users(id),
    match       integer REFERENCES matches(id),
    team        integer,
    value       decimal,
    items       numeric[],
    winnings    numeric[],
    state       bet_state,
    created_at  timestamp
);

CREATE INDEX ON bets USING GIN (items);
CREATE INDEX ON bets USING GIN (winnings);
CREATE INDEX on bets (state);


/*
  A trade
*/

CREATE TYPE trade_state AS ENUM ('NEW', 'IN-PROGRESS', 'OFFERED', 'ACCEPTED', 'REJECTED', 'UNKNOWN');
CREATE TYPE trade_type AS ENUM ('BET', 'RETURNS', 'INTERNAL');

CREATE TABLE trades (
  id          SERIAL PRIMARY KEY,
  offerid     integer,
  token       varchar(32) NOT NULL,
  state       trade_state NOT NULL,
  ttype       trade_type NOT NULL,
  to_id       numeric NOT NULL,
  message     text,
  items_in    numeric[] NOT NULL,
  items_out   numeric[] NOT NULL,
  created_at  timestamp,

  /* Optional References */
  bot_ref     integer REFERENCES bots(id),
  user_ref    integer REFERENCES users(id),
  bet_ref     integer REFERENCES bets(id),
);


/*
  A single item draft
*/

CREATE TYPE item_draft_state AS ENUM ('PENDING', 'STARTED', 'FAILED', 'COMPLETED', 'DISCARDED', 'USED');

CREATE TABLE item_drafts (
    id          SERIAL PRIMARY KEY,
    match       integer REFERENCES matches(id),
    team        integer REFERENCES teams(id),
    state       item_draft_state,
    started_at  timestamp,
    ended_at    timestamp
);

/*
  An exception
*/

CREATE TABLE exceptions (
  id          uuid PRIMARY KEY,
  etype       varchar(128),
  content     text,
  meta        jsonb,
  created_at  timestamp
);

CREATE INDEX ON exceptions (etype);

CREATE TABLE newsposts (
  id          SERIAL PRIMARY KEY,
  title       varchar(256) UNIQUE,
  category    varchar(256),
  content     text,
  meta        jsonb,
  is_public   boolean,
  created_at  timestamp,
  created_by  integer REFERENCES users(id)
);

CREATE INDEX ON newsposts (category);
CREATE INDEX ON newsposts (title);

CREATE TABLE bans (
    id           serial PRIMARY KEY,
    steamid      varchar(255),
    active       boolean,
    created_at   timestamp,
    start_date   timestamp,
    end_date     timestamp,
    reason       varchar(255),
    description  text,
    created_by   integer REFERENCES users(id)
);

CREATE INDEX ON bans(start_date, end_date);
