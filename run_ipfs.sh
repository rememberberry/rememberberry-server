# Start the daemon and init
ipfs daemon --init &

echo "Waiting until daemon is ready..."
# Wait until daemon is ready (it should listen to port 5001)
while ! curl --silent localhost:5001; do
  sleep 1
done

# Mount ipfs to the filesystem
ipfs mount --ipfs-path=/ipfs/
