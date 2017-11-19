# Note: ssl certs are copied into the docker image at build time
docker run \
  -p 443:443 \
  -p 80:80 \
  -v ~/.rememberberry_ipfs:/root/.ipfs \
  -ti rememberberry
