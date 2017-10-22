# Note: need the "privileged" option for fuse to work on osx
docker run \
  --privileged \
  --entrypoint=/bin/bash \
  -p 443:443 \
  -p 80:80 \
  -v ~/.rememberberry_ipfs:/root/.ipfs \
  -v $(pwd):/rememberberry-server \
  -v $(pwd)/../rememberscript:/rememberscript \
  -ti rememberberry
