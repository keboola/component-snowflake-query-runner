## Configuration specific parameters

The following parameters need to be specified in order to connect successfully to a Snowflake instance:

- `account` - Snowflake account name, [see Snowflake documentation for more information](https://docs.snowflake.com/en/user-guide/connecting.html#your-snowflake-account-name);
- `username` - Snowflake user, which will be used to log in to the instance;
- `#password` - password of the above specified Snowflake user;
- `warehouse` - name of the Snowflake warehouse, under which queries will run.

## Row specific parameters

Each row allows to specify query, which will be ran, as well as database and schema to be used. Parameters are:

- `database` - name of the Snowflake database to use;
- `schema` - Snowflake schema, where query will be ran;
- `query` - a query to run.