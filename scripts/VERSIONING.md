## Project versioning

In order to create a new version of the project with a change.log associated you need to:
* log your cahges into `scripts/wip_change.log``
* run 
    ```Bash
    cd scripts
    ./update-version.sh
    ```

The above will update the version, the change.log and do a commit with the new version as a description