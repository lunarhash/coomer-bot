import os
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError
import logging
from datetime import datetime

class DropboxSync:
    def __init__(self, access_token, refresh_token=None, app_key=None, app_secret=None, base_path="/coomer_videos"):
        """
        初始化 Dropbox 同步器
        :param access_token: Dropbox API access token
        :param refresh_token: Dropbox refresh token
        :param app_key: Dropbox app key
        :param app_secret: Dropbox app secret
        :param base_path: Dropbox 中的基础路径
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_path = base_path
        self.setup_logging()
        self.init_dropbox()

    def setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger('DropboxSync')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def init_dropbox(self):
        """初始化或刷新 Dropbox 客户端"""
        try:
            self.dbx = dropbox.Dropbox(self.access_token)
            # 测试连接
            self.dbx.users_get_current_account()
        except dropbox.exceptions.AuthError:
            if self.refresh_token and self.app_key and self.app_secret:
                self.logger.info("Access token expired, refreshing...")
                try:
                    self.dbx = dropbox.Dropbox(
                        oauth2_refresh_token=self.refresh_token,
                        app_key=self.app_key,
                        app_secret=self.app_secret
                    )
                    self.access_token = self.dbx._oauth2_access_token
                    self.logger.info("Successfully refreshed access token")
                except Exception as e:
                    self.logger.error(f"Failed to refresh token: {str(e)}")
                    raise
            else:
                self.logger.error("Unable to refresh access token without refresh token and app credentials")
                raise

    def get_dropbox_path(self, local_path):
        """
        将本地路径转换为 Dropbox 路径
        """
        rel_path = os.path.basename(local_path)
        return f"{self.base_path}/{rel_path}"

    async def upload_file(self, local_path, callback=None):
        """
        上传文件到 Dropbox
        :param local_path: 本地文件路径
        :param callback: 进度回调函数
        :return: 是否成功
        """
        try:
            dropbox_path = self.get_dropbox_path(local_path)
            file_size = os.path.getsize(local_path)
            
            # 检查文件是否已存在
            try:
                metadata = self.dbx.files_get_metadata(dropbox_path)
                self.logger.info(f"文件已存在: {dropbox_path}")
                if metadata.size == file_size:
                    self.logger.info("文件大小相同，跳过上传")
                    if callback:
                        await callback(local_path, True, "已存在")
                    return True
            except dropbox.exceptions.ApiError as e:
                if not isinstance(e.error, dropbox.files.GetMetadataError):
                    raise

            # 上传文件
            self.logger.info(f"开始上传: {local_path} -> {dropbox_path}")
            
            with open(local_path, 'rb') as f:
                self.dbx.files_upload(
                    f.read(),
                    dropbox_path,
                    mode=WriteMode('overwrite')
                )

            if callback:
                await callback(local_path, True, "上传成功")
            
            self.logger.info(f"上传完成: {dropbox_path}")
            return True

        except Exception as e:
            self.logger.error(f"上传失败 {local_path}: {str(e)}")
            if callback:
                await callback(local_path, False, str(e))
            return False

    async def sync_directory(self, local_dir, callback=None):
        """
        同步整个目录到 Dropbox
        :param local_dir: 本地目录路径
        :param callback: 进度回调函数
        :return: (成功数, 失败数)
        """
        success_count = 0
        failed_count = 0

        for root, _, files in os.walk(local_dir):
            for filename in files:
                if filename.lower().endswith(('.mp4', '.mov', '.avi', '.wmv', '.flv')):
                    local_path = os.path.join(root, filename)
                    if await self.upload_file(local_path, callback):
                        success_count += 1
                    else:
                        failed_count += 1

        return success_count, failed_count

    def create_share_link(self, dropbox_path):
        """
        创建文件的分享链接
        :param dropbox_path: Dropbox 中的文件路径
        :return: 分享链接
        """
        try:
            shared_link_metadata = self.dbx.sharing_create_shared_link_with_settings(dropbox_path)
            return shared_link_metadata.url
        except Exception as e:
            self.logger.error(f"创建分享链接失败: {str(e)}")
            return None

    def get_storage_usage(self):
        """
        获取存储使用情况
        :return: (已用空间, 总空间) 单位为字节
        """
        try:
            space_usage = self.dbx.users_get_space_usage()
            return space_usage.used, space_usage.allocation.get_individual().allocated
        except Exception as e:
            self.logger.error(f"获取存储使用情况失败: {str(e)}")
            return None, None
