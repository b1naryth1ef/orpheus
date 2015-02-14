/*
    CSGO Emporium Backend Database Schema
*/

/*
  Represents steam items in the database
*/

CREATE TABLE itemtypes (
  id SERIAL PRIMARY KEY,
  name text NOT NULL UNIQUE,
  price decimal,
  /* May be able to remove this field... */
  meta jsonb
);

CREATE INDEX ON itemtypes (name);


/*
  Represents a single item in the database

  owner: steamid, can be null
  price: cached price, can be null
*/

CREATE TYPE item_state AS ENUM ('UNKNOWN', 'EXTERNAL', 'INTERNAL', 'LOCKED');

CREATE TABLE items (
  id numeric PRIMARY KEY,
  owner bigint,
  type_id integer REFERENCES itemtypes(id),
  class_id integer NOT NULL,
  instance_id integer NOT NULL,
  price decimal,
  state item_state,
  meta jsonb
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
  id SERIAL PRIMARY KEY,
  steamid character varying(255) NOT NULL UNIQUE,
  email character varying(255) UNIQUE,
  active boolean,
  join_date timestamp with time zone,
  last_login timestamp with time zone,
  ugroup user_group,
  settings jsonb
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

CREATE TYPE bot_status AS ENUM ('NEW', 'COOLDOWN', 'AVAIL', 'USED', 'INVALID');

CREATE TABLE bots (
    id SERIAL PRIMARY KEY,
    steamid character varying(255),
    username character varying(255),
    password character varying(255),
    apikey character varying(32),
    sentry bytea,
    status bot_status,
    inventory numeric[],
    last_activity timestamp with time zone,
    active boolean
);

CREATE INDEX ON bots (inventory);


/*
  Represents crawled steam_guard_codes
    email: the email the steam_guard_code was sent too
    username: the username the steam_guard_code is for
    code: the actual code
*/

CREATE TABLE steam_guard_codes (
    id SERIAL PRIMARY KEY,
    email character varying(255),
    username character varying(255),
    code character varying(5)
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
    id SERIAL PRIMARY KEY,
    name character varying(255) NOT NULL,
    meta jsonb,
    appid integer,
    view_perm user_group,
    active boolean,
    created_by integer REFERENCES users(id),
    created_at timestamp with time zone
);


/*
  Represents a team
*/

CREATE TABLE teams (
  id SERIAL PRIMARY KEY,
  tag varchar(24) UNIQUE,
  name text,
  logo text,
  meta jsonb,
  created_by integer REFERENCES users(id),
  created_at timestamp with time zone
);


/*
  Represents a match played on a game for which there is a result and bets
    game: the game reference
    teams: a list of NON-FOREIGN references to teams
    players: a list of NON-FOREIGN references to users
    meta: metadata (e.g. media, streams)
    lock_date: when this match will lock bets
    match_date: when this match is actually being played
    public_date: when this match goes public
    view_perm: what user group can view this
    active: whether this is active
    created_by: user created by
    created_at: when this was created
*/

CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    game integer REFERENCES games(id),
    teams integer[],
    meta jsonb,
    results jsonb,
    max_value_item decimal,
    max_value_total decimal,
    lock_date timestamp with time zone,
    match_date timestamp with time zone,
    public_date timestamp with time zone,
    view_perm user_group,
    active boolean,
    created_by integer REFERENCES users(id),
    created_at timestamp with time zone,
    results_by integer REFERENCES users(id),
    results_at timestamp with time zone,
    items_at timestamp with time zone,
    draft_started_at timestamp with time zone,
    draft_finished_at timestamp with time zone,
    items_distributed boolean
);


/*
  Represents a bet placed on a match
*/

CREATE TYPE bet_state AS ENUM ('NEW', 'CONFIRMED', 'WON', 'LOST', 'CANCELLED');

CREATE TABLE bets (
    id SERIAL PRIMARY KEY,
    better integer REFERENCES users(id),
    match integer REFERENCES matches(id),
    team integer,
    value integer,
    items numeric[],
    winnings numeric[],
    state bet_state,
    created_at timestamp with time zone
);

CREATE INDEX ON bets (items);
CREATE INDEX ON bets (winnings);
CREATE INDEX on bets (state);


/*
  A trade
*/

CREATE TYPE trade_state AS ENUM ('NEW', 'IN-PROGRESS', 'OFFERED', 'ACCEPTED', 'REJECTED', 'UNKNOWN');
CREATE TYPE trade_type AS ENUM ('BET', 'RETURNS', 'INTERNAL');

CREATE TABLE trades (
  id SERIAL PRIMARY KEY,
  offerid integer,
  state trade_state,
  ttype trade_type,
  to_id numeric NOT NULL,
  message text,
  items_in numeric[],
  items_out numeric[],
  created_at timestamp with time zone,

  /* Optional References */
  bot_ref integer REFERENCES bots(id),
  user_ref integer REFERENCES users(id),
  bet_ref integer REFERENCES bets(id)
);


/*
  A single item draft
*/

CREATE TYPE item_draft_state AS ENUM ('PENDING', 'STARTED', 'FAILED', 'COMPLETED', 'DISCARDED', 'USED');

CREATE TABLE item_drafts (
    id SERIAL PRIMARY KEY,
    match integer REFERENCES matches(id),
    team integer REFERENCES teams(id),
    state item_draft_state,
    started_at timestamp with time zone,
    ended_at timestamp with time zone
);

