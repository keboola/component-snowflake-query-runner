## Configuration-Specific Parameters

The following parameters need to be specified to connect successfully to a Snowflake instance:

- `account`: Snowflake account name, [see Snowflake documentation for more information](https://docs.snowflake.com/en/user-guide/connecting.html#your-snowflake-account-name)
- `username`: Snowflake user that will be used to log in to the instance
- `#password`: Password for the specified Snowflake user
- `warehouse`: Name of the Snowflake warehouse where queries will run

## Row-Specific Parameters

Each row allows to specify a query to be run, as well as a database and schema to be used. Parameters are:

- `database`: Name of the Snowflake database to use
- `schema`: Snowflake schema where the query will be run
- `query`: Query to execute