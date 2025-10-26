#!/bin/bash
# Build script for Lambda layer with common dependencies

set -e

LAYER_NAME="accessibility-checker-dependencies"
PYTHON_VERSION="3.11"
ARCHITECTURE="x86_64"

echo "🔨 Building Lambda layer: $LAYER_NAME"

# Create build directory
BUILD_DIR="build/layer"
mkdir -p $BUILD_DIR

# Copy requirements file
cp layers/python/requirements.txt $BUILD_DIR/

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r $BUILD_DIR/requirements.txt -t $BUILD_DIR/python/

# Remove unnecessary files to reduce layer size
echo "🧹 Cleaning up unnecessary files..."
find $BUILD_DIR -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find $BUILD_DIR -type f -name "*.pyc" -delete 2>/dev/null || true
find $BUILD_DIR -type f -name "*.pyo" -delete 2>/dev/null || true
find $BUILD_DIR -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find $BUILD_DIR -type d -name "test" -exec rm -rf {} + 2>/dev/null || true
find $BUILD_DIR -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true

# Remove large unnecessary files
find $BUILD_DIR -name "*.so" -size +1M -delete 2>/dev/null || true
find $BUILD_DIR -name "*.a" -delete 2>/dev/null || true

# Create layer zip
echo "📦 Creating layer zip..."
cd $BUILD_DIR
zip -r ../../layer.zip . -q
cd ../..

# Get layer size
LAYER_SIZE=$(du -h layer.zip | cut -f1)
echo "✅ Layer created: layer.zip (Size: $LAYER_SIZE)"

# Deploy layer to AWS (optional)
if [ "$1" = "--deploy" ]; then
    echo "🚀 Deploying layer to AWS..."
    aws lambda publish-layer-version \
        --layer-name $LAYER_NAME \
        --description "Common dependencies for Accessibility Checker API" \
        --zip-file fileb://layer.zip \
        --compatible-runtimes python$PYTHON_VERSION \
        --compatible-architectures $ARCHITECTURE
    
    echo "✅ Layer deployed successfully!"
    echo "📝 Add this layer ARN to your Lambda functions"
fi

echo "🎉 Layer build completed!"
