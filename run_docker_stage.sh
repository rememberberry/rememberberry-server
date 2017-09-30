docker run -p 443:443 -p 80:80 -v ~/.ipfs:/root/.ipfs -v $(pwd):/rememberberry-server-stage --entrypoint=/bin/bash -ti rememberberry
