{
    "repository": {
        "repositoryArn": "arn:aws:ecr:us-east-1:231399652064:repository/chatterbox-tts",
        "registryId": "231399652064",
        "repositoryName": "chatterbox-tts",
        "repositoryUri": "231399652064.dkr.ecr.us-east-1.amazonaws.com/chatterbox-tts",
        "createdAt": "2026-02-09T23:16:31.646000-05:00",
        "imageTagMutability": "MUTABLE",
        "imageScanningConfiguration": {
            "scanOnPush": false
        },
        "encryptionConfiguration": {
            "encryptionType": "AES256"
        }
    }
}
