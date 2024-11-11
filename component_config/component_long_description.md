# Snowflake Query Runner

This application enables users to run any query against their Snowflake warehouse straight from Keboola.

It is row-based, meaning it accepts configuration-specific parameters used by each row run: account, username, #password, and warehouse. Each row allows you to specify a query to be run, as well as a database and schema to be used.