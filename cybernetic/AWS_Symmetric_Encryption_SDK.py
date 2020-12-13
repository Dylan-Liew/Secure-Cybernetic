import aws_encryption_sdk
import base64

# key_arn: Amazon Resource Name (ARN) of the KMS CMK
key_arn = 'arn:aws:kms:us-east-1:470238209779:key/8b9f00de-b78d-41d9-b0c0-4b8167fa8f1c'


def encrypt(plaintext, botocore_session=None):
    plaintext = str(plaintext).encode('utf-8')
    # Create a KMS master key provider.
    kms_kwargs = dict(key_ids=[key_arn])
    if botocore_session is not None:
        kms_kwargs['botocore_session'] = botocore_session
    master_key_provider = aws_encryption_sdk.KMSMasterKeyProvider(**kms_kwargs)

    # Encrypt the plaintext source data.
    ciphertext, encryptor_header = aws_encryption_sdk.encrypt(
        source=plaintext,
        key_provider=master_key_provider
    )
    ciphertext = base64.b64encode(ciphertext).decode('utf-8')
    return ciphertext


def decrypt(ciphertext, botocore_session=None):
    ciphertext = base64.b64decode(ciphertext.encode('utf-8'))
    # Create a KMS master key provider.
    kms_kwargs = dict(key_ids=[key_arn])
    if botocore_session is not None:
        kms_kwargs['botocore_session'] = botocore_session
    master_key_provider = aws_encryption_sdk.KMSMasterKeyProvider(**kms_kwargs)

    # Decrypt the ciphertext.
    plaintext, decrypted_header = aws_encryption_sdk.decrypt(
        source=ciphertext,
        key_provider=master_key_provider
    )
    plaintext = plaintext.decode("utf-8")
    return plaintext

