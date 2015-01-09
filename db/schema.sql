/*
    CSGO Emporium Backend Database Schema
    VERSION: 1
*/

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

CREATE TYPE bot_status AS ENUM ('NOAUTH', 'AVAIL', 'USED');
ALTER TYPE bot_status OWNER TO emporium;

CREATE TABLE accounts (
    id SERIAL,
    steamid character varying(255),
    username character varying(255),
    password character varying(255),
    sentry bytea,
    status bot_status,
    last_activity timestamp with time zone,
    active boolean
);
ALTER TABLE accounts OWNER TO emporium;

/*
  Represents crawled steam_guard_codes
    email: the email the steam_guard_code was sent too
    username: the username the steam_guard_code is for
    code: the actual code
*/

CREATE TABLE steam_guard_codes (
    id SERIAL,
    email character varying(255),
    username character varying(255),
    code character varying(5)
);
ALTER TABLE steam_guard_codes OWNER TO emporium;
