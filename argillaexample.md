Deploy with Docker
This guide describes how to deploy the Argilla Server with docker compose. This is useful if you want to deploy Argilla locally, and/or have full control over the configuration the server, database, and search engine (Elasticsearch).

First, you need to install docker on your machine and make sure you can run docker compose.

Then, create a folder (you can modify the folder name):

mkdir argilla && cd argilla
Download docker-compose.yaml:

wget -O docker-compose.yaml https://raw.githubusercontent.com/argilla-io/argilla/main/examples/deployments/docker/docker-compose.yaml
or using curl:

curl https://raw.githubusercontent.com/argilla-io/argilla/main/examples/deployments/docker/docker-compose.yaml -o docker-compose.yaml
Run to deploy the server on http://localhost:6900:

docker compose up -d
Once is completed, go to this URL with your browser: http://localhost:6900 and you should see the Argilla login page.

If it's not available, check the logs:

docker compose logs -f
Most of the deployment issues are related to ElasticSearch. Join Hugging Face Discord's server and ask for support on the Argilla channel.
