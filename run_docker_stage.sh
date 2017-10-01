# Note: need the "privileged" option for fuse to work on osx
docker run -p 443:443 -p 80:80 -v ~/.ipfs:/.ipfs -v $(pwd):/rememberberry-server-stage --privileged --entrypoint=/bin/bash -ti rememberberry
