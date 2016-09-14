CREATE TABLE public.users (
  id INTEGER PRIMARY KEY NOT NULL DEFAULT nextval('users_id_seq'::regclass),
  name CHARACTER VARYING(12) NOT NULL,
  passhash CHARACTER VARYING(128) NOT NULL
);
CREATE UNIQUE INDEX users_id_uindex ON users USING BTREE (id);
CREATE UNIQUE INDEX users_name_uindex ON users USING BTREE (name);