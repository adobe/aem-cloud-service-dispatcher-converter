# AEM as a Cloud Service - Dispatcher Conversion Report
This report contains the changes that have been made to your dispatcher configurations by the converter.  After reviewing these changes, you should simply run the dispatcher validator on the new configurations, with the `dispatcher` subcommand: `validator dispatcher .` to check the state. For any error, see the [Troubleshooting](./TroubleShooting.md) section of the
validator tool documentation.
#### Test your configuration with a local deployment (requires Docker installation)

Using the script `docker_run.sh` in the Dispatcher SDK, you can test that
your configuration does not contain any other error that would only show up in 
deployment:

##### Step 1: Generate deployment information with the validator

```
validator full -d out .
```
This validates the full configuration and generates deployment information in `out`

##### Step 2: Start the dispatcher in a docker image with that deployment information

With your AEM publish server running on your macOS computer, listening on port 4503,
you can run start the dispatcher in front of that server as follows:
``` 
$ docker_run.sh out docker.for.mac.localhost:4503 8080
```
This will start the container and expose Apache on local port 8080.

If the validator no longer reports any issue and the docker container starts up without
any failures or warnings, you're ready to move your configuration to a `dispatcher/src`
subdirectory of your git repository.


## Dispatcher Configuration changes

The structure of the project's dispatcher configurations folder should be as shown bellow :
```./
├── conf.d
│   ├── available_vhosts
│   │   └── default.vhost
│   ├── dispatcher_vhost.conf
│   ├── enabled_vhosts
│   │   ├── README
│   │   └── default.vhost -> ../available_vhosts/default.vhost
│   └── rewrites
│   │   ├── default_rewrite.rules
│   │   └── rewrite.rules
│   └── variables
|       ├── custom.vars
│       └── global.vars
└── conf.dispatcher.d
    ├── available_farms
    │   └── default.farm
    ├── cache
    │   ├── default_invalidate.any
    │   ├── default_rules.any
    │   └── rules.any
    ├── clientheaders
    │   ├── clientheaders.any
    │   └── default_clientheaders.any
    ├── dispatcher.any
    ├── enabled_farms
    │   ├── README
    │   └── default.farm -> ../available_farms/default.farm
    ├── filters
    │   ├── default_filters.any
    │   └── filters.any
    ├── renders
    │   └── default_renders.any
    └── virtualhosts
        ├── default_virtualhosts.any
        └── virtualhosts.any
```

For conversion of the provided configurations to Dispatcher configuration for AEM as a Cloud Service, we have made the following changes to the dispatcher configuration:
