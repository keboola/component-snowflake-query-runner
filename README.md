# Snowflake Query Runner

The application allows users to run any query against their Snowflake warehouse straight from Keboola.

**Table of contents:**  
  
[TOC]

# Configuration

The application is row-based and thus accepts configuration specific parameters, which are then used by each row ran.

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

## Development

If required, change local data folder (the `CUSTOM_FOLDER` placeholder) path to your custom path in the docker-compose file:

```yaml
    volumes:
      - ./:/code
      - ./CUSTOM_FOLDER:/data
```

Clone this repository, init the workspace and run the component with following command:

```
git clone repo_path my-new-component
cd my-new-component
docker-compose build
docker-compose run --rm dev
```

Run the test suite and lint check using this command:

```
docker-compose run --rm test
```

# Integration

For information about deployment and integration with KBC, please refer to the [deployment section of developers documentation](https://developers.keboola.com/extend/component/deployment/) 