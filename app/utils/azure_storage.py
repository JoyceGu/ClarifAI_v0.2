"""
Azure Blob Storage工具
"""
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from flask import current_app
import uuid
import os
from datetime import datetime, timedelta
from azure.storage.blob import generate_blob_sas, BlobSasPermissions

# 全局变量
blob_service_client = None
container_client = None

def init_blob_service(app):
    """初始化Blob Storage服务"""
    global blob_service_client, container_client
    
    connection_string = app.config.get('AZURE_STORAGE_CONNECTION_STRING')
    container_name = app.config.get('AZURE_STORAGE_CONTAINER_NAME', 'file-uploads')
    
    if not connection_string:
        app.logger.warning("Azure Storage connection string not configured.")
        return
        
    try:
        # 创建BlobServiceClient对象
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # 获取或创建容器
        try:
            container_client = blob_service_client.get_container_client(container_name)
            # 检查容器是否存在，如果不存在会引发异常
            container_client.get_container_properties()
        except Exception:
            # 容器不存在，创建新容器
            container_client = blob_service_client.create_container(
                name=container_name,
                public_access='blob'  # 设置为blob级别的公共访问
            )
            app.logger.info(f"Created new container: {container_name}")
            
        app.logger.info(f"Azure Blob Storage initialized with container: {container_name}")
    except Exception as e:
        app.logger.error(f"Failed to initialize Azure Blob Storage: {str(e)}")
        blob_service_client = None
        container_client = None
        
def upload_file_to_blob(file_data, original_filename, content_type=None):
    """上传文件到Blob Storage"""
    if not blob_service_client or not container_client:
        current_app.logger.error("Azure Blob Storage not initialized")
        return None
        
    try:
        # 生成唯一的blob名称
        unique_filename = f"{str(uuid.uuid4())}_{original_filename}"
        
        # 创建blob客户端
        blob_client = blob_service_client.get_blob_client(
            container=container_client.container_name,
            blob=unique_filename
        )
        
        # 上传文件
        blob_client.upload_blob(file_data, overwrite=True, content_settings={
            'content_type': content_type,
            'content_disposition': f'attachment; filename="{original_filename}"'
        })
        
        # 返回blob的URL和唯一文件名
        return {
            'url': blob_client.url,
            'filename': unique_filename,
            'blob_name': unique_filename
        }
    except Exception as e:
        current_app.logger.error(f"Error uploading file to Azure Blob Storage: {str(e)}")
        return None
        
def get_blob_url(blob_name, with_sas_token=False, expiry_hours=1):
    """获取blob的URL，可选带SAS令牌"""
    if not blob_service_client or not container_client:
        current_app.logger.error("Azure Blob Storage not initialized")
        return None
    
    try:
        blob_client = blob_service_client.get_blob_client(
            container=container_client.container_name,
            blob=blob_name
        )
        
        if with_sas_token:
            # 生成SAS令牌
            sas_token = generate_blob_sas(
                account_name=blob_service_client.account_name,
                container_name=container_client.container_name,
                blob_name=blob_name,
                account_key=blob_service_client.credential.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
            )
            
            # 返回带有SAS令牌的URL
            return f"{blob_client.url}?{sas_token}"
        else:
            # 返回公共URL
            return blob_client.url
    
    except Exception as e:
        current_app.logger.error(f"Error generating blob URL: {str(e)}")
        return None
        
def delete_blob(blob_name):
    """删除blob"""
    if not blob_service_client or not container_client:
        current_app.logger.error("Azure Blob Storage not initialized")
        return False
        
    try:
        blob_client = blob_service_client.get_blob_client(
            container=container_client.container_name,
            blob=blob_name
        )
        
        # 删除blob
        blob_client.delete_blob()
        return True
    except Exception as e:
        current_app.logger.error(f"Error deleting blob: {str(e)}")
        return False 