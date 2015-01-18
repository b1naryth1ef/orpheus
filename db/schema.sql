/*
    CSGO Emporium Backend Database Schema
*/

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

CREATE TYPE user_group AS ENUM ('normal', 'moderator', 'admin', 'super');

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  steamid character varying(255) NOT NULL UNIQUE,
  email character varying(255) UNIQUE,
  active boolean,
  join_date timestamp,
  last_login timestamp,
  ugroup user_group,
  settings jsonb
);

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

CREATE TYPE bot_status AS ENUM ('COOLDOWN', 'NOAUTH', 'AVAIL', 'USED');

CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    steamid character varying(255),
    username character varying(255),
    password character varying(255),
    sentry bytea,
    status bot_status,
    last_activity timestamp,
    inventory text[],
    active boolean
);


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
    appid: the steam appid
    view_perm: the user group that can view this
    active: whether this is active
    created_by: user created by
    created_at: when this was created
*/

CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    name character varying(255) NOT NULL,
    appid integer,
    view_perm user_group,
    active boolean,
    created_by integer REFERENCES users(id),
    created_at timestamp
);

/*
  Represents a team who plays a game
    game: the game this team plays
    name: the team name
    tag: the team tag
    meta: metadata (logos/websites/etc) about the team
    active: whether this is active
    created_by: user created by
    created_at: when this was created
*/

CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    game integer REFERENCES games(id),
    name character varying(255) NOT NULL,
    tag character varying(12) NOT NULL,
    meta jsonb,
    active boolean,
    created_by integer REFERENCES users(id),
    created_at timestamp
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
    players integer[],
    meta jsonb,
    lock_date timestamp,
    match_date timestamp,
    public_date timestamp,
    view_perm user_group,
    active boolean,
    created_by integer REFERENCES users(id),
    created_at timestamp
);


/*
  Represents the result of a match. Seperate mostly for auditing purposes.
*/

CREATE TABLE match_results (
    id SERIAL PRIMARY KEY,
    results jsonb,
    match integer REFERENCES matches(id),
    created_by integer REFERENCES users(id),
    created_at timestamp
);


/*
  Represents a bet placed on a match
*/

CREATE TABLE bets (
    id SERIAL PRIMARY KEY,
    better integer REFERENCES users(id),
    match integer REFERENCES matches(id),
    team integer REFERENCES teams(id),
    items jsonb,
    returns jsonb
);


/*
  Represents steam trades in the database
*/

CREATE TYPE trade_type AS ENUM ('returns', 'winnings');
CREATE TYPE trade_state AS ENUM ('offered', 'declined', 'accepted', 'cancelled');

CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    account integer REFERENCES accounts(id),
    trader integer REFERENCES users(id),
    bot_out jsonb,
    bot_in jsonb,
    state trade_state,
    ttype trade_type,
    created_at timestamp
);

