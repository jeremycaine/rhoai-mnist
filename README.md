# Red Hat OpenShift AI and MNIST Image Recognition
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
    - project: `jeremycaine-dev`

## Create a Data Science Project workbench
Red Hat OpenShift AI
- Data science projects
    - Project: `jeremycaine-dev`
        - Workbenches > Create Workbench > `mnist-workbench`
    - Image: `Jupyter | TensorFlow | CUDA | Python 3.12`, py 3.12`
    - Container Size: Small
    - "Create workbench"

We will come back to update this with a connection to the object storage.

Launch the workbench.

## Create the Object Storage
We will create a MinIO object storage bucket and connect our OpenShift cluster to it. The steps to do this were originally taken from [here](https://developers.redhat.com/learning/learn:openshift-ai:automate-ml-pipeline-openshift-ai/resource/resources:set-and-execute-pipeline)

Back in the Red Hat OpenShift AI console, go to the top right 3x3 square and launch the OpenShift Console.

Red Hat OpenShift
- Open terminal `>_`
```
git clone https://github.com/jeremycaine/rhoai-mnist
cd rhoai-mnist/build-and-deploy/
oc create -f minio.yaml
```
This creates the MinIO deployment, the persistent volume claim and various Kubernetes objects to attach the object storage to the cluster.

## Upload the MNIST data files
We will load the data files we got from Kaggle into a MinIO bucket.

Launch MinIO from with in the Red Hat OpenShift (Service on AWS)

Red Hat OpenShift
- Networking > Routes
- select `jeremycaine-dev`project
- Route `minio-ui` > Location URL for console
- In the MinIO app
- Username and password: `miniosandbox`
- Create bucket: `mnist-ml`
- Create a new path (folde): `data`
- upload the two MNIST CSV files

Also create a simple text file e.g. `hello.txt` and load it into the `data` folder.

Note the Route `minio-api` Location URL.

## Update the Workbench
Go to Red Hat OpenShift AI
- Data science project > `jeremycaine-dev`
    - Workbench: `mnist-workbench` > three dots - Edit Workbench
    - Create a Connection
        - S3 connection type
        - Name: `conn-minio`
        - Access and Secret Keys: `miniosandbox`
        - Region: `us-east-1`
        - Bucket Name: `mnist-ml`
    - "Update workbench"

Open VINO Model Server embeds the AWS S3 SDK to make its S3 connections to different object storage. The AWS S3 SDK used by OVMS requires a non-empty region value for signing and endpoint formatting `us-east-1` is the only one that historically works without needing special endpoint signing rules.

The creation of this connection automatically sets the environment variables you will use in the code to access the bucket. They are:

- AWS_S3_ENDPOINT
- AWS_S3_BUCKET
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_DEFAULT_REGION

## Clone the Git repo into the workbench
In JupyterHub
- Git
- Clone a Repository (include subfolders; but no need to download)
    - https://github.com/jeremycaine/rhoai-mnist

Now in the JupyterHub file browser, you'll see the repo files.

## Train the model
Open up the notebook `build-and-deploy/train-model.ipynb`

You can run piece by piece to see the TensorFlow model building or do the whole thing. At the end of the training we upload the model in Keras format to object storage, and convert it to ONNX format and upload that.

## Create a model server
The goal has been to deploy the model to the OpenShift AI platform model serving functions. There are a variety of these including Generative AI model serving.

In the sandbox environment there is one type available Open VINO Model Server (OVMS).

Go to Red Hat OpenShift AI
- Data science project > `jeremycaine-dev`
    - Models
        - Add Model Server
            - Moder server name: `mnist-model-server`
            - Serving runtime: OpenVINO Model Server (only option in sandbox)
            - Number of replicas: 1 is fine for this experiment
            - Model server size: Small 
            - Model route: make it external
            - Token authentication: leave this off for now.

Token authentication is the secure recommendation. A Bearer token is required in the HTTPS call to the model endpoint URL.

## Deploy a model
The OpenVINO Model Server has been configured in the sandbox with 'Multi-model serving enabled'. For production platforms requiring different scale of inference you can have single model serving enabled and optimise specifically for one model.

Now we can deploy model to the model server. We have two model formats in our object storage `.keras` and `.onnx`.

Go to Red Hat OpenShift AI
- Models
    - Model Deployment
        - Deploy Model
            - Model deployment name: e.g. `mnist-onnx`
            - Model server will be picked
            - Model framework e.g. `onnx - 1` for ONNX, and `tensorflow - 2` for Keras
            - Connection - existing connection
            - "Deploy"

You can use the existing one for the model server to connect to the model file. Again in production environment you will probably have a more sophisticated setup an dedicated secured connection for serving the models for throughput and performance reasones.

## Model endpoint
Once the models are started you have internal and external facing endpoints. Clicking on that hotlink will reveal the URIs.

Internal (accessible only from inside the cluster)
- grpcUrl: grpc://modelmesh-serving.jeremycaine-dev:8033
- restUrl: http://modelmesh-serving.jeremycaine-dev:8008

External (accessible from inside or outside the cluster)
- https://mnist-keras-jeremycaine-dev.apps.rm2.thpm.p1.openshiftapps.com/v2/models/mnist-keras/infer


## Deploy an app to use the model
We have an image recognition web app. It takes a HTML canvas where you can use the mouse to hand draw anything. On submit, it calls the model inference and attempts to classify what is drawn against a digit from 0-9.

Red Hat OpenShift Console
- top right (+)
- Import from Git
    - Git repo URL: https://github.com/jeremycaine/rhoai-mnist
    - Context dir: image-rec-app
    - Import strategy: Dockerfile (it finds `src` dir and Dockerfile and self-selects)
    - Application name: overwrite with with what is auto-generated e.g. `image-rec-app-app` to `image-rec-app`
    - Build - leave as is
    - Deploy - resource type: Deployment
        - app name: `rhoai-mnist-app`
        - set an env var for the deployment e.g.
        - OVMS_URL = https://mnist-onxx-jeremycaine-dev.apps.rm2.thpm.p1.openshiftapps.com/v2/models/mnist-onxx/infer 
    - Target port: e.g. 8080
    - "Create"

The Build process now begins. The Route is created to the app.

Once complete check Workload > Deployments e.g. `rhoai-mnist-app`

Then in Networking > Routes you will find the route URL
e.g. https://rhoai-mnist-app-jeremycaine-dev.apps.rm2.thpm.p1.openshiftapps.com 

Go to the web app and test !