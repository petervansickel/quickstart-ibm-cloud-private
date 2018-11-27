# Using TaskCat to deploy the IBM Cloud Private QuickStart

TaskCat is a command line tool for deploying QuickStarts to the AWS cloud.

See [Automated testing with TaskCat](https://aws-quickstart.github.io/auto-testing.html) for details on TaskCat.

See [Installing TaskCat](https://aws-quickstart.github.io/install-taskcat.html) for TaskCat installation instructions.

QuickStarts are all tested using TaskCat so any QuickStart must conform to the requirements for running TaskCat to execute QuickStart tests.

# QuickStart git repository

The QuickStart git repository has a certain structure that is expected by TaskCat.

If you are using the Eclipse project to work on the ICP QuickStart scripts, then you will need to copy the content from the IBM git repository to the ICP QuickStart repository.  There is an Ant script to do so named: `CopyToQuickStartRepo.xml`.  Run this Ant script to move the latest content to the ICP QuickStart git repository.


# Using TaskCat for the ICP QuickStart deployment

- Be sure you have the latest content in the ICP QuickStart git repository.

- Command line samples:
```
taskcat -n -c ~/git/quickstart-ibm-cloud-private/ci/taskcat-us-e1.yaml 2>&1 | tee logs/taskcat-2018-1106-05.log
```
