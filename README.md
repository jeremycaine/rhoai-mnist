# rhoai-mnist
Building MNIST image recognition with Red Hat OpenShift AI. This hello word dataset and CNN model is a collection of handwritten digits between 0-9. A web app with a drawing canvas captures a hand drawn digit, and infers from the model as to what the digit is.

## Source the MNIST Image data
Get the MNIST Train and Test CSV

https://www.kaggle.com/datasets/oddrationale/mnist-in-csv 

Put the data files `mnist_test.csv` and `mnist_train.csv` in a folder that can be uploaded to a MinIO bucket later.

## Red Hat Developer Sandbox
Go to the [sandbox site](https://developers.redhat.com/developer-sandbox).

Go to the 'Try it' for OpenShift AI. It automatically creates you a project namespace in OpenShift using your Red Hat login name. It then creates a data science project within that.

Red Hat OpenShift AI
- Home
- Data science projects
    - project: jeremycaine-dev


## Create Object Storage
We will create a MinIO object storage bucket and connect our OpenShift cluster to it. The steps to do this were originally taken from [here](https://developers.redhat.com/learning/learn:openshift-ai:automate-ml-pipeline-openshift-ai/resource/resources:set-and-execute-pipeline)



put mnist csv files in minio

Minio
Taken from 

3x3 top right
Red Hat OpenShift Console
- open terminal `>_`
```
git clone https://github.com/utherp0/aipipeline1
cd aipipeline1
oc create -f minio.yaml
```
- Networking > Routes
- select jeremycaine-dev project
- Route minio-ui > Location URL for console
- u/p: miniosandbox
- create bucket: mnist-pipeline
- create a new path (folde): data
- upload MNIST files

Create a connection to Minio in workbench
- connection type: S3 compatible
- connection name: conn-minio
- access and secret keys: miniosandbox
- bucket name: mnist-pipeline

## OpenShift Container Platform
We need to create external environment variables in the cluster for the OpenShift AI project to reference e.g. interacting with the MinIO object storage.

## data science
Red Hat OpenShift AI
- Data Science Projects > jeremycaine-dev (assigned by Sandbox)
- Workbenches > Create Workbench > rhoai-mnist
    - image: Data science, py 3.12
    - container size: small
    - attach connection - conn-minio -s3 - minio
    - Environment Variables
        - MINIO_HOST: minio-api-utherp0-dev.apps.rm1.0a51.p1.openshiftapps.com
        - MINIO_USER: miniosandbox
        - MINIO_PWD: miniosandbox



## Notebooks
Launch workbench, now in Jupyter Lab
Create notebooks



## pipeline

## model server


## app in openshift cluster
can it all be done in sandbox?

## routes
curl -vk https://minio-api-jeremycaine-dev.apps.rm2.thpm.p1.openshiftapps.com/minio/health/ready = ok

