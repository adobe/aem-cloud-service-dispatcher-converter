# AEM Cloud Service Dispatcher Converter

AEM Dispatcher Converter is a tool for converting existing AEM Dispatcher configurations to AEM as a Cloud Service Dispatcher configurations.

### Goals

The goal of this project is to make it as simple as possible for AEM developers to migrate existing AEM Dispatcher configurations to the cloud.

### Non-Goals

This project is specifically focused on AEM Dispatcher configurations.  While there are other types of migrations that may also be necessary for a customer to migrate to the cloud, they would be considered outside of the scope of this particular project.


### Implementing Dispatcher Converter

The **AEMDispatcherConverter** follows the conversion guidelines.

Refer to [Converting an AMS to an Adobe Experience Manager as a Cloud Service Dispatcher Configuration](https://docs.adobe.com/content/help/en/experience-manager-cloud-service/implementing/content-delivery/disp-overview.html#how-to-convert-an-ams-to-an-aem-as-a-cloud-service-dispatcher-configuration) for converting Adobe Managed Services Dispatcher Configurations v2.0 to AEM as a Cloud Service Dispatcher Configurations.

   >[NOTE]
   > The utility assumes that the Adobe Managed Services dispatcher configurations provided is of v2.0. Customers who are using v1.0 configurations should contact Customer Support to get help for migrating from v1.0 to v2.0.


### Usage

The usage considerations for Dispatcher Converter are:

* Developed using Python 3.7.3.
  It is recommended to have Python 3.5 or above installed.

* The `main.py` module requires 2 parameters to be executed

	* **--cfg** : Absolute path to dispatcher config folder (make sure the immediate sub-folders start with `conf`, `conf.d`, `conf.dispatcher.d` and `conf.modules.d`
	* **--sdk_src** : Absolute path to the `src` folder of the dispatcher sdk

	**On Windows Environment**

	```shell
	python main.py --sdk_src=C:\Users\xyz\Desktop\Dispatcher\dispatcher-sdk-2.0.20\src --cfg=C:\Users\xyz\Desktop\Dispatcher\entegris
	```

	**On Unix Environment**

	```shell
	python3 main.py --sdk_src=/Users/xyz/Desktop/Dispatcher/dispatcher-sdk-2.0.20/src --cfg=/Users/xyz/Desktop/Dispatcher/entegris
	```
* The actions performed during the conversion are logged in `result.log` which is created in the same directory where `main.py` resides.

### Limitations

The AEM Dispatcher Converter has the following limitations:

* AEM Dispatcher Converter works on the assumption that the provided dispatcher configuration folder's structure is similar to the one described in [Cloud Manager Dispatcher Configurations](https://docs.adobe.com/content/help/en/experience-manager-cloud-manager/using/getting-started/dispatcher-configurations.html).

* AEM Dispatcher Converter is not integrated with the [AEM as a Cloud Service Dispatcher Validator](https://docs.adobe.com/content/help/en/experience-manager-learn/cloud-service/local-development-environment-set-up/dispatcher-tools.html). 

   Running the validator tool on the converted dispatcher configurations is required manually.

#### Running the Dispatcher Validator

>[NOTE]
> For more information on Dispatcher Validator, refer to [Adobe Experience Manager as a Cloud Service SDK](https://docs.adobe.com/content/help/en/experience-manager-learn/cloud-service/local-development-environment-set-up/dispatcher-tools.html).

1. Run the dispatcher validator on the converted configurations, with the `dispatcher` sub-command:
   ```java
   $ validator dispatcher
   ```

1. If you encounter errors about missing include files, check whether you correctly renamed those files.

1. If you see errors concerning undefined variable `PUBLISH_DOCROOT`, rename it to `DOCROOT`.

For troubleshooting other errors, refer to [Troubleshooting & Local Validation of Dispatcher Configuration](https://docs.adobe.com/content/help/en/experience-manager-learn/cloud-service/local-development-environment-set-up/dispatcher-tools.html#troubleshooting).


#### Development Considerations

* On-premise dispatcher configurations are quite specific to individual customers as well as the in-house expertise of the customer. Therefore, no generic steps for transition are currently defined.

* To extend this converter to transition any customer's on-premise dispatcher configuration :

  * Define the steps for transition following which one can convert the on-premise configurations to AEM as a Cloud Service dispatcher configurations.
  
    Refer to [Converting an AMS to an Adobe Experience Manager as a Cloud Service Dispatcher configuration](https://docs.adobe.com/content/help/en/experience-manager-cloud-service/implementing/content-delivery/disp-overview.html#how-to-convert-an-ams-to-an-aem-as-a-cloud-service-dispatcher-configuration) for more details.

  * In the `converter` directory, implement the rules of transition in a new converter class (for reference see `AEMDispatcherConverter`)
  using the generic file and folder manipulation utilities provided under `util` directory. 
  
    Refer to [Utilities](./util/utilities.md) for the check-list of utilities methods.
  
    >[NOTE]
    > Use the utility methods which best suits the operation/step that you need to perform for the transition. In the event that they do not cater to your needs, you can implement the required operation:
    > modify `main.py` to use the new converter (instead of `AEMDispatcherConverter`) to perform the transition.

### Contributing

Contributions are welcomed! Read the [Contributing Guide](./.github/CONTRIBUTING.md) for more information.

### Licensing

This project is licensed under the Apache V2 License. See [LICENSE](LICENSE) for more information.