# Note: -L option for copying to dereference symlinks, as docker ADD doesnt
# support symlinks
rm -rf docker/certs
cp -Lr /etc/letsencrypt/live/bot.rememberberry.com docker/certs
if [ ! -f docker/certs ]; then
  mkdir docker/certs
fi
docker build --build-arg CACHE_DATE="$(date)" -t rememberberry docker/
