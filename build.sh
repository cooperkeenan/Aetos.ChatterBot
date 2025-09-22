#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="facebook-messenger"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Building Facebook Messenger (AMD64) ===${NC}"

# Build for AMD64 (Azure VM architecture)
echo -e "${YELLOW}Building for AMD64 platform...${NC}"
docker buildx build \
    --platform linux/amd64 \
    --tag ${IMAGE_NAME}:latest \
    .

echo -e "${GREEN}=== Build Complete! ===${NC}"

# Show usage
echo ""
echo "Usage:"
echo "  Test:       docker-compose --profile test up messenger-test"
echo "  Production: docker-compose up facebook-messenger"
echo ""
echo "To push to registry:"
echo "  docker tag ${IMAGE_NAME}:latest your-registry/${IMAGE_NAME}:latest"
echo "  docker push your-registry/${IMAGE_NAME}:latest"