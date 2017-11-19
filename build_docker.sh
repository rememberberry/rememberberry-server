# Note: -L option for copying to dereference symlinks, as docker ADD doesnt
# support symlinks
rm -rf docker/certs
cp -Lr /etc/letsencrypt/live/bot.rememberberry.com docker/certs
docker build --build-arg CACHE_DATE="$(date)" -t rememberberry docker/
