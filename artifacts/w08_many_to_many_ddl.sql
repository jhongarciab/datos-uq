CREATE TABLE planet_demo(
  planet_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL
);

CREATE TABLE method_demo(
  method_id INTEGER PRIMARY KEY,
  method_name TEXT NOT NULL UNIQUE
);

CREATE TABLE planet_method_demo(
  planet_id INTEGER NOT NULL,
  method_id INTEGER NOT NULL,
  PRIMARY KEY (planet_id, method_id),
  FOREIGN KEY (planet_id) REFERENCES planet_demo(planet_id),
  FOREIGN KEY (method_id) REFERENCES method_demo(method_id)
);
