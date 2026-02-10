#!/bin/bash
# Fix S3 bucket permissions for public access to voice files

echo "🔧 Fixing S3 bucket permissions for Chatterbox TTS..."

BUCKET_NAME="chatterbox-audio-231399652064"
AWS_REGION="us-east-1"

echo "📋 Setting up S3 bucket: $BUCKET_NAME"

# 1. Set bucket public access policy
echo "🔓 Setting bucket policy for public read access to voices..."
aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadVoices",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": [
        "arn:aws:s3:::'"$BUCKET_NAME"'/chatterbox/voices/*",
        "arn:aws:s3:::'"$BUCKET_NAME"'/chatterbox/audio/*"
      ]
    }
  ]
}' --region "$AWS_REGION"

# 2. Disable block public access for this bucket (needed for public read)
echo "🔓 Updating public access block settings..."
aws s3api put-public-access-block --bucket "$BUCKET_NAME" --public-access-block-configuration \
  BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false \
  --region "$AWS_REGION"

# 3. Set CORS policy for Vercel frontend access
echo "🌐 Setting CORS policy for Vercel access..."
aws s3api put-bucket-cors --bucket "$BUCKET_NAME" --cors-configuration '{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "HEAD"],
      "AllowedOrigins": [
        "https://*.vercel.app",
        "https://*.vercel.sh", 
        "http://localhost:3000",
        "https://localhost:3000"
      ],
      "ExposeHeaders": ["ETag", "Content-Length"],
      "MaxAgeSeconds": 3600
    }
  ]
}' --region "$AWS_REGION"

echo ""
echo "🧪 Testing voice file accessibility..."
sleep 2

# Test Andrew Tate voice file
VOICE_URL="https://$BUCKET_NAME.s3.$AWS_REGION.amazonaws.com/chatterbox/voices/andrew_tate.mp4"
echo "Testing: $VOICE_URL"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$VOICE_URL")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Andrew Tate voice file is publicly accessible"
    echo "📏 File size: $(curl -sI "$VOICE_URL" | grep -i content-length | cut -d' ' -f2 | tr -d '\r')"
else
    echo "❌ Voice file still not accessible (HTTP $HTTP_CODE)"
    echo "🔍 Checking bucket policy..."
    aws s3api get-bucket-policy --bucket "$BUCKET_NAME" --region "$AWS_REGION" || echo "No bucket policy found"
fi

echo ""
echo "📋 S3 Voice Files Available:"
aws s3 ls "s3://$BUCKET_NAME/chatterbox/voices/" --region "$AWS_REGION"

echo ""
echo "✅ S3 configuration complete!"
echo ""
echo "🔗 Voice URLs for your application:"
echo "   Andrew Tate: https://$BUCKET_NAME.s3.$AWS_REGION.amazonaws.com/chatterbox/voices/andrew_tate.mp4"
echo "   Trump: https://$BUCKET_NAME.s3.$AWS_REGION.amazonaws.com/chatterbox/voices/trump_voice.mp4"
echo "   Peter Griffin: https://$BUCKET_NAME.s3.$AWS_REGION.amazonaws.com/chatterbox/voices/peterg.mp4"
echo "   Lois Griffin: https://$BUCKET_NAME.s3.$AWS_REGION.amazonaws.com/chatterbox/voices/lois_voice.mp4"