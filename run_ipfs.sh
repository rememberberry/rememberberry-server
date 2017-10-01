# Start the daemon
ipfs daemon &

# Wait until daemon is ready (it should listen to port 5001)
while ! curl --silent localhost:5001; do
  sleep 1
done

# Mount ipfs to the filesystem
ipfs mount --ipfs-path=/ipfs/
