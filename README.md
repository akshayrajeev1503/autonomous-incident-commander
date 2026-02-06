# autonomous-incident-commander
Hackathon

![architecture](architecture.png)

docker buildx build \
  --platform linux/arm64 \
  --provenance=false \
  --output type=docker \
  -t logging-lambda .