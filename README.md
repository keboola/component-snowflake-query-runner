# Snowflake Query Runner

Snowflake offers a cloud-based data storage and analytics service known as "data warehouse-as-a-service", allowing users to store and analyze data using cloud-based hardware and software.

This application enables you to run any query against your Snowflake warehouse directly from the Keboola platform.

**Table of contents:**  
  
[TOC]

# Configuration

The application is row-based, and as such, accepts configuration-specific parameters used by each row run.

## Configuration-Specific Parameters

The following parameters need to be specified to connect successfully to a Snowflake instance:

- `account`: Snowflake account name [(see Snowflake documentation for more information)](https://docs.snowflake.com/en/user-guide/connecting.html#your-snowflake-account-name)
- `username`: Snowflake user that will be used to log in to the instance
- `warehouse`: Name of the Snowflake warehouse where queries will be run
- `auth_type`: Authentication method to use. Can be either:
  - `key_pair` (default): Use key-pair authentication
  - `password`: Use password-based authentication

For key-pair authentication:
- `#private_key`: Private key for authentication
- `#private_key_passphrase`: (Optional) Passphrase for the private key

For password-based authentication:
- `#password`: Password for the specified Snowflake user

Note: Only one authentication method can be used at a time - either password or key-pair authentication.

## Row-Specific Parameters

Each row allows to specify a query to be run, as well as a database and schema to be used. Parameters are:

- `database`: Name of the Snowflake database to use
- `schema`: Snowflake schema where the query will be run
- `query`: Query to execute

## Development

If needed, change the path to the local data folder (the `CUSTOM_FOLDER` placeholder) in the docker-compose file:

```yaml
    volumes:
      - ./:/code
      - ./CUSTOM_FOLDER:/data
```

Clone this repository, initialize the workspace, and run the component with the following commands:

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

For information about deployment and integration with Keboola, please refer to the [deployment section of the developer documentation](https://developers.keboola.com/extend/component/deployment/). 