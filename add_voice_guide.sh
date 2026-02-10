#!/bin/bash
# Quick script to upload voice audio to S3 and update config

# Configuration
AUDIO_FILE="$1"  # Path to your audio file
VOICE_ID="$2"    # ID for the voice (e.g., "my_voice")
VOICE_NAME="$3"  # Display name (e.g., "My Voice Name")

# Validate inputs
if [ -z "$AUDIO_FILE" ] || [ -z "$VOICE_ID" ] || [ -z "$VOICE_NAME" ]; then
    echo "Usage: $0 <audio_file> <voice_id> <voice_name>"
    echo "Example: $0 myvoice.wav my_voice 'My Voice Name'"
    exit 1
fi

if [ ! -f "$AUDIO_FILE" ]; then
    echo "Error: Audio file '$AUDIO_FILE' not found"
    exit 1
fi

# S3 Configuration (from .env)
S3_BUCKET="chatterbox-audio-231399652064"
S3_PREFIX="chatterbox/voices"
AWS_REGION="us-east-1"

# Get file extension
EXT="${AUDIO_FILE##*.}"
S3_KEY="${S3_PREFIX}/${VOICE_ID}.${EXT}"

echo "📤 Uploading audio to S3..."
echo "   File: $AUDIO_FILE"
echo "   S3 Key: s3://${S3_BUCKET}/${S3_KEY}"

# Upload to S3
aws s3 cp "$AUDIO_FILE" "s3://${S3_BUCKET}/${S3_KEY}" \
    --region "$AWS_REGION" \
    --content-type "audio/${EXT}"

if [ $? -ne 0 ]; then
    echo "❌ Upload failed"
    exit 1
fi

# Generate public URL
AUDIO_URL="https://${S3_BUCKET}.s3.${AWS_REGION}.amazonaws.com/${S3_KEY}"

echo "✅ Upload successful!"
echo ""
echo "📋 Add this to your character_voices.json:"
echo ""
cat << EOF
{
  "voices": {
    "${VOICE_ID}": {
      "name": "${VOICE_NAME}",
      "language": "en",
      "audio_url": "${AUDIO_URL}",
      "description": "Description of this voice",
      "quality": "high",
      "tags": ["custom", "uploaded"]
    }
  }
}
EOF

echo ""
echo "🔗 Audio URL: ${AUDIO_URL}"
echo ""
echo "Next steps:"
echo "1. Add the voice config above to character_voices.json"
echo "2. Assign it to a character by setting 'voice_id': '${VOICE_ID}'"
echo "3. Restart your API server or redeploy to Render"
