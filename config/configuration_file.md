## Configuration File


Configuration file must contains at least the _DEFAULT_ section with the OCI config and _OCI_TOOLS_ section with the script configuration.
OCI configuration file are also supported with the command line parameter __--profile__ ___<profile_name>___

Below the list of supported value in the _OCI_TOOLS_ section

#### region_filter
Comma separated region to work on. 
Currently must not be empty.

```
region_filter=eu-frankfurt-1,uk-london-1
```

#### operation
> This parameter can be overridden by command line argument
available operation:
 - ___list___: scan the tenancy and list all the resources (Default)
 - ___cleanup___: delete all but toplevel compartments
 - ___dryrun___: emulate _cleanup_ without affect any resource
 - ___destroy___: delete all (NOT IMPLEMENTED)
 
```
operation=cleanup
```

#### preserve_compartments
Comma separated list of compartments to keep safe. The cleanup process ignores all the listed compartments and the resources that belong to them 
```
preserve_compartments=comp_1,comp_2
```

#### preserve_tags
comma separated list of tag to keep safe.  
The cleanup process ignores all the resources tagged with at least one of the listed tags
 - freeform tags must be inserted it the following format:  
    - _key=value_  
    - _key_
 - defined tags must be inserted in the following format: 
    - _namespace:key=value_
    
```
preserve_tags=training.foundation=true,safe=true,not_delete
```   

#### compartment_flter

Comma separated compartment OCID to limit the cleanup to. 
The cleanup process will consider only the listed compartments  
If empty all the compartment are terminated
```
compartment_flter=my_compartment
```

#### preserve_top_level_compartment
If true the cleanup script ignores the top level compartments  
In case compartment_filter is used then the compartments specified is considered as top level compartments  
___Default value___: _false_
```
preserve_top_level_compartment=true
```

#### preserve_compartments
Preserve the compartment structure. The cleanup script deletes all the resources but the compartments  
___Default value___: _false_
```
preserve_compartments=true
```



#### skip_scan_preserved_resources
if True don't inspect preserved resources (via _preserve_compartments_ or _preserve_tags_)
___Default value___: _true_
```
skip_scan_preserved_resources=false
```
 
